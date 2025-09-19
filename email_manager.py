import sqlite3
import threading
from datetime import datetime


class EmailManager:
    def __init__(self, db_path='automation_data.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize email management tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS email_config (
                    id INTEGER PRIMARY KEY,
                    base_email TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    starting_number INTEGER NOT NULL,
                    current_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS email_usage (
                    id INTEGER PRIMARY KEY,
                    email_address TEXT UNIQUE NOT NULL,
                    process_number INTEGER,
                    status TEXT DEFAULT 'active',
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    blacklisted_at TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_email_usage_status ON email_usage(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_email_usage_process ON email_usage(process_number)')
    
    def set_email_config(self, base_email, domain, starting_number):
        """Set or update email configuration"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Check if config exists
                existing = conn.execute('SELECT id FROM email_config LIMIT 1').fetchone()
                
                if existing:
                    # Update existing config
                    conn.execute('''
                        UPDATE email_config 
                        SET base_email = ?, domain = ?, starting_number = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (base_email, domain, starting_number, existing[0]))
                else:
                    # Insert new config
                    conn.execute('''
                        INSERT INTO email_config (base_email, domain, starting_number, current_number)
                        VALUES (?, ?, ?, ?)
                    ''', (base_email, domain, starting_number, starting_number))
                
                conn.commit()
                return True
    
    def get_email_config(self):
        """Get current email configuration"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute('SELECT * FROM email_config ORDER BY id DESC LIMIT 1').fetchone()
            return dict(result) if result else None
    
    def get_next_email(self, process_number):
        """Get the next available email for a process"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get current config
                config = conn.execute('SELECT * FROM email_config ORDER BY id DESC LIMIT 1').fetchone()
                if not config:
                    raise Exception("Email configuration not set. Please configure email settings first.")
                
                config = dict(config)
                
                # Find next available number
                current_number = config['current_number']
                email_address = f"{config['base_email']}{current_number}@{config['domain']}"
                
                # Check if email is already used
                existing = conn.execute('''
                    SELECT status FROM email_usage WHERE email_address = ?
                ''', (email_address,)).fetchone()
                
                if existing and existing[0] != 'completed':
                    # Find next available number
                    max_used = conn.execute('''
                        SELECT MAX(CAST(REPLACE(REPLACE(email_address, ?, ''), '@' || ?, '') AS INTEGER)) 
                        FROM email_usage 
                        WHERE email_address LIKE ?
                    ''', (config['base_email'], config['domain'], f"{config['base_email']}%@{config['domain']}")).fetchone()
                    
                    if max_used and max_used[0]:
                        current_number = max_used[0] + 1
                    else:
                        current_number = config['starting_number']
                    
                    email_address = f"{config['base_email']}{current_number}@{config['domain']}"
                
                # Reserve the email for this process
                conn.execute('''
                    INSERT OR REPLACE INTO email_usage (email_address, process_number, status, assigned_at)
                    VALUES (?, ?, 'active', CURRENT_TIMESTAMP)
                ''', (email_address, process_number))
                
                # Update current number in config
                conn.execute('''
                    UPDATE email_config 
                    SET current_number = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (current_number + 1, config['id']))
                
                conn.commit()
                
                return email_address
    
    def mark_email_completed(self, email_address):
        """Mark an email as completed (successful purchase)"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    UPDATE email_usage 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE email_address = ?
                ''', (email_address,))
                conn.commit()
    
    def mark_email_failed(self, email_address):
        """Mark an email as failed (can be reused)"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    DELETE FROM email_usage WHERE email_address = ?
                ''', (email_address,))
                conn.commit()
    
    def blacklist_email(self, email_address):
        """Blacklist an email (cannot be reused)"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO email_usage (email_address, process_number, status, blacklisted_at)
                    VALUES (?, NULL, 'blacklisted', CURRENT_TIMESTAMP)
                ''', (email_address,))
                conn.commit()
    
    def get_process_email(self, process_number):
        """Get the current email assigned to a specific process"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                SELECT email_address FROM email_usage 
                WHERE process_number = ? AND status = 'active'
                ORDER BY assigned_at DESC LIMIT 1
            ''', (process_number,)).fetchone()
            
            return result[0] if result else None
    
    def get_email_statistics(self):
        """Get email usage statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Count by status
            results = conn.execute('''
                SELECT status, COUNT(*) FROM email_usage GROUP BY status
            ''').fetchall()
            
            for status, count in results:
                stats[status] = count
            
            return stats
    
    def get_all_email_usage(self):
        """Get all email usage records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute('''
                SELECT * FROM email_usage ORDER BY assigned_at DESC
            ''').fetchall()
            
            return [dict(row) for row in results]
    
    def reset_email_system(self):
        """Reset the entire email system (clear all usage data)"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM email_usage')
                
                # Reset current number to starting number
                config = conn.execute('SELECT starting_number FROM email_config ORDER BY id DESC LIMIT 1').fetchone()
                if config:
                    conn.execute('''
                        UPDATE email_config 
                        SET current_number = starting_number, updated_at = CURRENT_TIMESTAMP
                    ''')
                
                conn.commit()
    
    def cleanup_failed_processes(self):
        """Clean up emails from processes that may have crashed"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                # Remove emails assigned more than 1 hour ago but still active
                conn.execute('''
                    DELETE FROM email_usage 
                    WHERE status = 'active' 
                    AND datetime(assigned_at) < datetime('now', '-1 hour')
                ''')
                conn.commit()