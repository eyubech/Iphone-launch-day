"""
Encrypted database manager for storing cards and pickup persons - Fixed Version
"""

import sqlite3
import json
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import random
from datetime import datetime
from email_manager import EmailManager

class DatabaseManager:
    def __init__(self, db_path="automation_data.db", master_password="default_key_2024"):
        self.db_path = db_path
        self.master_password = master_password
        self.cipher_suite = self._create_cipher_suite()
        self.init_database()
    
    def migrate_email_tables(self):
        try:
            email_manager = EmailManager(self.db_path)
            email_manager.create_email_tables()
            print("Email management tables created/updated successfully")
        except Exception as e:
            print(f"Error creating email tables: {e}")
    
    
    
    def _create_cipher_suite(self):
        """Create encryption cipher suite from master password"""
        password = self.master_password.encode()
        salt = b'salt_for_automation_2024'  # In production, use random salt per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def _encrypt_data(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher_suite.encrypt(data).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher_suite.decrypt(encrypted_data).decode()
    
    def init_database(self):
        """Initialize database tables with migration support"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Cards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    card_number TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    cvc TEXT NOT NULL,
                    billing_info TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Check if user_info column exists, add if not
            cursor.execute("PRAGMA table_info(cards)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'user_info' not in columns:
                cursor.execute('ALTER TABLE cards ADD COLUMN user_info TEXT')
                print("Added user_info column to cards table")
            
            # Pickup persons table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pickup_persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Check if is_primary column exists, add if not
            cursor.execute("PRAGMA table_info(pickup_persons)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'is_primary' not in columns:
                cursor.execute('ALTER TABLE pickup_persons ADD COLUMN is_primary BOOLEAN DEFAULT 0')
                print("Added is_primary column to pickup_persons table")
                
                # Set first person as primary if exists
                cursor.execute('SELECT id FROM pickup_persons WHERE is_active = 1 ORDER BY created_at ASC LIMIT 1')
                first_person = cursor.fetchone()
                if first_person:
                    cursor.execute('UPDATE pickup_persons SET is_primary = 1 WHERE id = ?', (first_person[0],))
                    print("Set first person as primary")
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zip_code TEXT NOT NULL,
                    street_address TEXT NOT NULL,
                    postal_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_default BOOLEAN DEFAULT 0
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def add_card(self, name, card_number, expiry_date, cvc, billing_info, user_info=None):
        """Add new card to database with optional user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Encrypt sensitive data
            encrypted_card = self._encrypt_data(card_number)
            encrypted_cvc = self._encrypt_data(cvc)
            encrypted_billing = self._encrypt_data(json.dumps(billing_info))
            
            # Handle user_info (might be None for backward compatibility)
            if user_info:
                encrypted_user = self._encrypt_data(json.dumps(user_info))
            else:
                encrypted_user = None
            
            # Check if user_info column exists
            cursor.execute("PRAGMA table_info(cards)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_info' in columns and encrypted_user:
                cursor.execute('''
                    INSERT INTO cards (name, card_number, expiry_date, cvc, billing_info, user_info)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, encrypted_card, expiry_date, encrypted_cvc, encrypted_billing, encrypted_user))
            else:
                cursor.execute('''
                    INSERT INTO cards (name, card_number, expiry_date, cvc, billing_info)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, encrypted_card, expiry_date, encrypted_cvc, encrypted_billing))
            
            conn.commit()
            card_id = cursor.lastrowid
            return card_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def add_pickup_person(self, name, first_name, last_name, email, phone, is_primary=None):
        """Add new pickup person to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if this is the first person (auto-primary)
            cursor.execute('SELECT COUNT(*) FROM pickup_persons WHERE is_active = 1')
            count = cursor.fetchone()[0]
            
            # If this is the first person or is_primary is explicitly True, make them primary
            if count == 0 or is_primary is True:
                is_primary = True
                # Remove primary flag from others if setting this one as primary
                cursor.execute('UPDATE pickup_persons SET is_primary = 0 WHERE is_active = 1')
            elif is_primary is None:
                is_primary = False
            
            # Check if is_primary column exists
            cursor.execute("PRAGMA table_info(pickup_persons)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_primary' in columns:
                cursor.execute('''
                    INSERT INTO pickup_persons (name, first_name, last_name, email, phone, is_primary)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, first_name, last_name, email, phone, is_primary))
            else:
                cursor.execute('''
                    INSERT INTO pickup_persons (name, first_name, last_name, email, phone)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, first_name, last_name, email, phone))
            
            conn.commit()
            person_id = cursor.lastrowid
            return person_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def add_settings(self, zip_code, street_address, postal_code, is_default=False):
        """Add location settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if is_default:
                # Remove default flag from other settings
                cursor.execute('UPDATE settings SET is_default = 0')
            
            cursor.execute('''
                INSERT INTO settings (zip_code, street_address, postal_code, is_default)
                VALUES (?, ?, ?, ?)
            ''', (zip_code, street_address, postal_code, is_default))
            
            conn.commit()
            setting_id = cursor.lastrowid
            return setting_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_all_cards(self):
        """Get all active cards with user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check what columns exist
        cursor.execute("PRAGMA table_info(cards)")
        columns = [column[1] for column in cursor.fetchall()]
        has_user_info = 'user_info' in columns
        
        cursor.execute('SELECT * FROM cards WHERE is_active = 1 ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        cards = []
        for row in rows:
            try:
                # Decrypt sensitive data
                card_number = self._decrypt_data(row[2])
                cvc = self._decrypt_data(row[4])
                billing_info = json.loads(self._decrypt_data(row[5]))
                
                # Handle user_info if column exists
                user_info = {}
                if has_user_info and len(row) > 6 and row[6]:
                    try:
                        user_info = json.loads(self._decrypt_data(row[6]))
                    except:
                        user_info = {}
                
                cards.append({
                    'id': row[0],
                    'name': row[1],
                    'card_number': card_number,
                    'expiry_date': row[3],
                    'cvc': cvc,
                    'billing_info': billing_info,
                    'user_info': user_info,
                    'created_at': row[7] if len(row) > 7 else row[6],
                    'masked_number': '*' * (len(card_number) - 4) + card_number[-4:]
                })
            except Exception as e:
                print(f"Error decrypting card {row[0]}: {e}")
                continue
        
        conn.close()
        return cards
    
    def get_all_pickup_persons(self):
        """Get all active pickup persons, primary first"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if is_primary column exists
        cursor.execute("PRAGMA table_info(pickup_persons)")
        columns = [column[1] for column in cursor.fetchall()]
        has_primary = 'is_primary' in columns
        
        if has_primary:
            cursor.execute('SELECT * FROM pickup_persons WHERE is_active = 1 ORDER BY is_primary DESC, created_at ASC')
        else:
            cursor.execute('SELECT * FROM pickup_persons WHERE is_active = 1 ORDER BY created_at ASC')
        
        rows = cursor.fetchall()
        
        persons = []
        for row in rows:
            # Handle both old and new table structures
            if has_primary and len(row) > 6:
                persons.append({
                    'id': row[0],
                    'name': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'is_primary': bool(row[6]),
                    'created_at': row[7] if len(row) > 7 else row[6]
                })
            else:
                # Old structure or missing is_primary
                is_primary = len(persons) == 0  # First person is primary
                persons.append({
                    'id': row[0],
                    'name': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'email': row[4],
                    'phone': row[5],
                    'is_primary': is_primary,
                    'created_at': row[6]
                })
        
        conn.close()
        return persons
    
    def get_all_settings(self):
        """Get all location settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM settings ORDER BY is_default DESC, created_at DESC')
        rows = cursor.fetchall()
        
        settings = []
        for row in rows:
            settings.append({
                'id': row[0],
                'zip_code': row[1],
                'street_address': row[2],
                'postal_code': row[3],
                'created_at': row[4],
                'is_default': bool(row[5])
            })
        
        conn.close()
        return settings
    
    def get_random_card(self):
        """Get random active card"""
        cards = self.get_all_cards()
        if not cards:
            return None
        return random.choice(cards)
    
    def get_primary_pickup_person(self):
        """Get the primary pickup person (first entered)"""
        persons = self.get_all_pickup_persons()
        if not persons:
            return None
        
        # Look for primary person first
        for person in persons:
            if person.get('is_primary', False):
                return person
        
        # Fallback to first person
        return persons[0]
    
    def get_default_settings(self):
        """Get default location settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM settings WHERE is_default = 1 LIMIT 1')
        row = cursor.fetchone()
        
        if row:
            conn.close()
            return {
                'id': row[0],
                'zip_code': row[1],
                'street_address': row[2],
                'postal_code': row[3],
                'is_default': bool(row[5])
            }
        
        # If no default, get first one
        cursor.execute('SELECT * FROM settings ORDER BY created_at DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'zip_code': row[1],
                'street_address': row[2],
                'postal_code': row[3],
                'is_default': bool(row[5])
            }
        
        return None
    
    def delete_card(self, card_id):
        """Soft delete card"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE cards SET is_active = 0 WHERE id = ?', (card_id,))
        conn.commit()
        conn.close()
    
    def delete_pickup_person(self, person_id):
        """Soft delete pickup person"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE pickup_persons SET is_active = 0 WHERE id = ?', (person_id,))
        conn.commit()
        conn.close()
    
    def delete_settings(self, setting_id):
        """Delete location settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM settings WHERE id = ?', (setting_id,))
        conn.commit()
        conn.close()
    
    def get_automation_data(self):
        """Get random card and primary pickup person for automation"""
        card = self.get_random_card()
        person = self.get_primary_pickup_person()  # Always use primary pickup person
        settings = self.get_default_settings()
        
        if not card or not person or not settings:
            missing = []
            if not card: missing.append("payment cards")
            if not person: missing.append("pickup persons")
            if not settings: missing.append("location settings")
            
            raise ValueError(f"Missing required data: {', '.join(missing)}")
        
        # Use card's user info if available, otherwise fallback to pickup person
        user_info = card.get('user_info', {})
        billing_info = card.get('billing_info', {})
        
        # Combine data for automation - prioritize card's associated user data
        automation_data = {
            'zip_code': settings['zip_code'],
            'first_name': user_info.get('first_name', person['first_name']),
            'last_name': user_info.get('last_name', person['last_name']),
            'email': user_info.get('email', person['email']),
            'phone': user_info.get('phone', person['phone']),
            'street_address': settings['street_address'],
            'postal_code': settings['postal_code'],
            'credit_card': card['card_number'],
            'expiry_date': card['expiry_date'],
            'cvc': card['cvc'],
            # Billing info from card
            'billing_first_name': billing_info.get('first_name', user_info.get('first_name', person['first_name'])),
            'billing_last_name': billing_info.get('last_name', user_info.get('last_name', person['last_name'])),
            'billing_street_address': billing_info.get('street_address', settings['street_address']),
            'billing_postal_code': billing_info.get('postal_code', settings['postal_code'])
        }
        
        return automation_data, card, person, settings