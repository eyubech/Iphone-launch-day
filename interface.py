import tkinter as tk
from tkinter import ttk, messagebox
import threading
import multiprocessing
import psutil
import requests
import random
from email_manager import EmailManager


class BrightDataProxy:
    def __init__(self, config):
        self.zone_id = config.BRIGHT_DATA_ZONE_ID
        self.username = config.BRIGHT_DATA_USERNAME
        self.endpoint = config.BRIGHT_DATA_ENDPOINT
        self.port = config.BRIGHT_DATA_PORT
        self.enabled = False
        
    def generate_session_id(self, process_num=1):
        return f"session_{process_num}_{random.randint(1000, 9999)}"
    
    def get_proxy_auth(self, process_num=1):
        session_id = self.generate_session_id(process_num)
        auth_username = f"{self.username}-session-{session_id}"
        return f"{auth_username}:{self.zone_id}"
    
    def get_proxy_url(self, process_num=1):
        session_id = self.generate_session_id(process_num)
        auth_username = f"{self.username}-session-{session_id}"
        return f"http://{auth_username}:{self.zone_id}@{self.endpoint}:{self.port}"
    
    def test_proxy(self, process_num=1):
        try:
            session_id = self.generate_session_id(process_num)
            auth_username = f"{self.username}-session-{session_id}"
            auth_password = self.zone_id
            
            proxy_url = f"http://{auth_username}:{auth_password}@{self.endpoint}:{self.port}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            print(f"Testing proxy: {self.endpoint}:{self.port}")
            print(f"Auth username: {auth_username}")
            print(f"Zone ID: {self.zone_id[:10]}...")
            
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get('origin', 'Connected')
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.ProxyError as e:
            error_msg = str(e)
            if "407" in error_msg:
                return False, "Proxy authentication failed: Check credentials in config.py"
            elif "403" in error_msg:
                return False, "Access forbidden: Check zone permissions"
            elif "404" in error_msg:
                return False, "Endpoint not found: Check endpoint URL"
            else:
                return False, f"Proxy error: {error_msg}"
        except requests.exceptions.ConnectTimeout:
            return False, "Connection timeout - check endpoint and port"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: Check internet connection"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_chrome_proxy_options(self, process_num=1):
        if not self.enabled:
            return []
        
        session_id = self.generate_session_id(process_num)
        auth_username = f"{self.username}-session-{session_id}"
        
        return [
            f"--proxy-server=http://{self.endpoint}:{self.port}",
            f"--proxy-auth={auth_username}:{self.zone_id}",
            "--disable-web-security",
            "--ignore-certificate-errors"
        ]
    
    def enable_proxy(self):
        self.enabled = True
    
    def disable_proxy(self):
        self.enabled = False
    
    def is_enabled(self):
        return self.enabled


class CleanModernGUI:
    def __init__(self):
        try:
            from config import Config
            from database import DatabaseManager
            from apple_automation import AppleAutomation
            
            self.config = Config()
            self.db = DatabaseManager()
            self.AppleAutomation = AppleAutomation
            self.email_manager = EmailManager()
        except ImportError as e:
            messagebox.showerror("Import Error", f"Missing required files: {str(e)}")
            return
            
        self.root = tk.Tk()
        self.automation = None
        self.automation_thread = None
        self.active_processes = []
        self.max_processes = self._calculate_max_processes()
        self.continuous_mode = False
        self._stopped = False
        self.proxy = BrightDataProxy(self.config)
        
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def _calculate_max_processes(self):
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        max_by_cpu = max(1, cpu_count // 2)
        max_by_memory = max(1, int(memory_gb // 1.5))
        return min(max_by_cpu, max_by_memory, 8)

    def setup_window(self):
        self.root.title("Apple iPhone Automation Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(True, True)
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Success.TButton', font=('Arial', 9, 'bold'), foreground='white', background='#10b981')
        style.configure('Primary.TButton', font=('Arial', 9, 'bold'), foreground='white', background='#2563eb')
        style.configure('Danger.TButton', font=('Arial', 9), foreground='white', background='#ef4444')
        style.configure('Warning.TButton', font=('Arial', 9), foreground='white', background='#f59e0b')
        
    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="iPhone Automation Pro", 
                               font=('Arial', 18, 'bold'), foreground='#2563eb')
        title_label.pack(side=tk.LEFT)
        
        self.stats_frame = ttk.Frame(header_frame)
        self.stats_frame.pack(side=tk.RIGHT)
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.create_automation_tab()
        self.create_cards_tab()
        self.create_persons_tab()
        self.create_settings_tab()
        self.create_automation_tab()
        self.create_email_manager_tab()

        
        self.update_stats()
    
    def load_data(self):
        self.refresh_card_list()
        self.refresh_person_list()
        self.refresh_settings()
        self.refresh_email_statistics()
        self.refresh_email_usage()
        self.update_email_preview()
        self.update_selection_labels()
        
        
    def refresh_email_statistics(self):
        try:
            stats = self.email_manager.get_email_statistics()
            config = self.email_manager.get_email_config()
            
            self.email_stats_text.config(state='normal')
            self.email_stats_text.delete(1.0, tk.END)
            
            stats_text = "Email System Statistics:\n\n"
            
            if config:
                stats_text += f"Base Email: {config['base_email']}\n"
                stats_text += f"Domain: {config['domain']}\n"
                stats_text += f"Starting Number: {config['starting_number']}\n"
                stats_text += f"Current Number: {config['current_number']}\n\n"
            
            stats_text += "Email Usage:\n"
            stats_text += f"Active: {stats.get('active', 0)}\n"
            stats_text += f"Completed: {stats.get('completed', 0)}\n"
            stats_text += f"Blacklisted: {stats.get('blacklisted', 0)}\n"
            stats_text += f"Total Used: {sum(stats.get(key, 0) for key in ['active', 'completed', 'blacklisted'])}"
            
            self.email_stats_text.insert(1.0, stats_text)
            self.email_stats_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh email statistics: {str(e)}")

    def refresh_email_usage(self):
        try:
            # Clear existing items
            for item in self.email_usage_tree.get_children():
                self.email_usage_tree.delete(item)
            
            usage_data = self.email_manager.get_all_email_usage()
            
            for usage in usage_data:
                process_text = f"Process {usage['process_number']}" if usage['process_number'] else "Manual"
                status = usage['status'].title()
                assigned_time = usage['assigned_at'][:16] if usage['assigned_at'] else "N/A"
                
                self.email_usage_tree.insert('', 'end', values=(
                    usage['email_address'],
                    process_text,
                    status,
                    assigned_time
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh email usage: {str(e)}")

    def reset_email_system(self):
        try:
            if messagebox.askyesno("Confirm Reset", 
                                "This will delete ALL email usage data and reset the system.\n\nAre you sure?"):
                self.email_manager.reset_email_system()
                self.refresh_email_statistics()
                self.refresh_email_usage()
                self.update_email_preview()
                messagebox.showinfo("Success", "Email system reset successfully!")
                self.log_message("Email system reset - all usage data cleared")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset email system: {str(e)}")

    def blacklist_manual_email(self):
        try:
            email = self.manual_email_var.get().strip()
            if not email:
                messagebox.showerror("Error", "Please enter an email address")
                return
            
            if '@' not in email:
                messagebox.showerror("Error", "Please enter a valid email address")
                return
            
            self.email_manager.blacklist_email(email)
            self.manual_email_var.set("")
            self.refresh_email_statistics()
            self.refresh_email_usage()
            messagebox.showinfo("Success", f"Email {email} has been blacklisted")
            self.log_message(f"Email blacklisted: {email}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to blacklist email: {str(e)}")
    def create_email_manager_tab(self):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Email Manager")
        
        main_frame = ttk.Frame(tab_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Email Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Email Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        config_frame.columnconfigure(1, weight=1)
        
        ttk.Label(config_frame, text="Base Email:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.base_email_var = tk.StringVar(value="billing")
        base_email_entry = ttk.Entry(config_frame, textvariable=self.base_email_var, font=('Arial', 9), width=20)
        base_email_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(0, 10))
        
        ttk.Label(config_frame, text="Domain:", font=('Arial', 9, 'bold')).grid(
            row=0, column=2, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.domain_var = tk.StringVar(value="garraje.com")
        domain_entry = ttk.Entry(config_frame, textvariable=self.domain_var, font=('Arial', 9), width=20)
        domain_entry.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(0, 10))
        
        ttk.Label(config_frame, text="Starting Number:", font=('Arial', 9, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.starting_number_var = tk.IntVar(value=10)
        starting_number_spinbox = ttk.Spinbox(config_frame, from_=1, to=9999, 
                                            textvariable=self.starting_number_var, width=10)
        starting_number_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(0, 10))
        
        save_config_btn = ttk.Button(config_frame, text="Save Configuration", 
                                command=self.save_email_config, style='Success.TButton')
        save_config_btn.grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        
        reset_system_btn = ttk.Button(config_frame, text="Reset Email System", 
                                    command=self.reset_email_system, style='Danger.TButton')
        reset_system_btn.grid(row=1, column=3, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Email Preview
        preview_frame = ttk.Frame(config_frame)
        preview_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(preview_frame, text="Email Preview:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.email_preview_label = ttk.Label(preview_frame, text="billing10@garraje.com", 
                                        font=('Arial', 10), foreground='#2563eb')
        self.email_preview_label.pack(anchor=tk.W, pady=2)
        
        # Email Statistics
        stats_frame = ttk.LabelFrame(main_frame, text="Email Statistics", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 15), padx=(0, 7))
        
        self.email_stats_text = tk.Text(stats_frame, height=8, width=40, font=('Arial', 9), 
                                    bg='#f8f9fa', state='disabled')
        self.email_stats_text.pack(fill=tk.BOTH, expand=True)
        
        refresh_stats_btn = ttk.Button(stats_frame, text="Refresh Statistics", 
                                    command=self.refresh_email_statistics, style='Primary.TButton')
        refresh_stats_btn.pack(pady=(10, 0))
        
        # Email Usage List
        usage_frame = ttk.LabelFrame(main_frame, text="Email Usage History", padding="10")
        usage_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), pady=(0, 15), padx=(7, 0))
        usage_frame.columnconfigure(0, weight=1)
        usage_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for email usage
        columns = ('Email', 'Process', 'Status', 'Assigned')
        self.email_usage_tree = ttk.Treeview(usage_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.email_usage_tree.heading(col, text=col)
            if col == 'Email':
                self.email_usage_tree.column(col, width=200)
            elif col == 'Process':
                self.email_usage_tree.column(col, width=70)
            elif col == 'Status':
                self.email_usage_tree.column(col, width=100)
            else:
                self.email_usage_tree.column(col, width=150)
        
        usage_scrollbar = ttk.Scrollbar(usage_frame, orient=tk.VERTICAL, command=self.email_usage_tree.yview)
        self.email_usage_tree.configure(yscrollcommand=usage_scrollbar.set)
        
        self.email_usage_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        usage_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        refresh_usage_btn = ttk.Button(usage_frame, text="Refresh Usage", 
                                    command=self.refresh_email_usage, style='Primary.TButton')
        refresh_usage_btn.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # Manual Email Management
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Email Management", padding="10")
        manual_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        manual_frame.columnconfigure(1, weight=1)
        
        ttk.Label(manual_frame, text="Email Address:", font=('Arial', 9)).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.manual_email_var = tk.StringVar()
        manual_email_entry = ttk.Entry(manual_frame, textvariable=self.manual_email_var, 
                                    font=('Arial', 9), width=30)
        manual_email_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        
        blacklist_manual_btn = ttk.Button(manual_frame, text="Blacklist Email", 
                                        command=self.blacklist_manual_email, style='Danger.TButton')
        blacklist_manual_btn.grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Load initial data
        self.load_email_config()
        self.refresh_email_statistics()
        self.refresh_email_usage()

    def save_email_config(self):
        """Save email configuration"""
        try:
            base_email = self.base_email_var.get().strip()
            domain = self.domain_var.get().strip()
            starting_number = self.starting_number_var.get()
            
            if not base_email or not domain:
                messagebox.showerror("Error", "Please fill all email configuration fields")
                return
            
            success = self.email_manager.set_email_config(base_email, domain, starting_number)
            
            if success:
                self.update_email_preview()
                self.refresh_email_statistics()
                messagebox.showinfo("Success", "Email configuration saved!")
                self.log_message(f"Email config updated: {base_email}@{domain} starting from {starting_number}")
            else:
                messagebox.showerror("Error", "Failed to save email configuration")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save email configuration: {str(e)}")

    def load_email_config(self):
        """Load existing email configuration"""
        try:
            config = self.email_manager.get_email_config()
            if config:
                self.base_email_var.set(config['base_email'])
                self.domain_var.set(config['domain'])
                self.starting_number_var.set(config['starting_number'])
                self.update_email_preview()
        except Exception as e:
            print(f"Error loading email config: {e}")

    def update_email_preview(self):
        """Update the email preview display"""
        try:
            config = self.email_manager.get_email_config()
            if config:
                preview_email = f"{config['base_email']}{config['current_number']}@{config['domain']}"
                self.email_preview_label.config(text=f"Next: {preview_email}")
        except Exception as e:
            print(f"Error updating email preview: {e}")

    def refresh_email_statistics(self):
        """Refresh email statistics display"""
        try:
            stats = self.email_manager.get_email_statistics()
            config = self.email_manager.get_email_config()
            
            self.email_stats_text.config(state='normal')
            self.email_stats_text.delete(1.0, tk.END)
            
            stats_text = "Email System Statistics:\n\n"
            
            if config:
                stats_text += f"Base Email: {config['base_email']}\n"
                stats_text += f"Domain: {config['domain']}\n"
                stats_text += f"Starting Number: {config['starting_number']}\n"
                stats_text += f"Current Number: {config['current_number']}\n\n"
            
            stats_text += "Email Usage:\n"
            stats_text += f"Active: {stats.get('active', 0)}\n"
            stats_text += f"Completed: {stats.get('completed', 0)}\n"
            stats_text += f"Blacklisted: {stats.get('blacklisted', 0)}\n"
            stats_text += f"Total Used: {sum(stats.get(key, 0) for key in ['active', 'completed', 'blacklisted'])}"
            
            self.email_stats_text.insert(1.0, stats_text)
            self.email_stats_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh email statistics: {str(e)}")

    def refresh_email_usage(self):
        """Refresh email usage list"""
        try:
            # Clear existing items
            for item in self.email_usage_tree.get_children():
                self.email_usage_tree.delete(item)
            
            usage_data = self.email_manager.get_all_email_usage()
            
            for usage in usage_data:
                process_text = f"Process {usage['process_number']}" if usage['process_number'] else "Manual"
                status = usage['status'].title()
                assigned_time = usage['assigned_at'][:16] if usage['assigned_at'] else "N/A"
                
                self.email_usage_tree.insert('', 'end', values=(
                    usage['email_address'],
                    process_text,
                    status,
                    assigned_time
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh email usage: {str(e)}")

    def reset_email_system(self):
        """Reset the entire email system"""
        try:
            if messagebox.askyesno("Confirm Reset", 
                                "This will delete ALL email usage data and reset the system.\n\nAre you sure?"):
                self.email_manager.reset_email_system()
                self.refresh_email_statistics()
                self.refresh_email_usage()
                self.update_email_preview()
                messagebox.showinfo("Success", "Email system reset successfully!")
                self.log_message("Email system reset - all usage data cleared")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset email system: {str(e)}")

    def blacklist_manual_email(self):
        """Manually blacklist an email address"""
        try:
            email = self.manual_email_var.get().strip()
            if not email:
                messagebox.showerror("Error", "Please enter an email address")
                return
            
            if '@' not in email:
                messagebox.showerror("Error", "Please enter a valid email address")
                return
            
            self.email_manager.blacklist_email(email)
            self.manual_email_var.set("")
            self.refresh_email_statistics()
            self.refresh_email_usage()
            messagebox.showinfo("Success", f"Email {email} has been blacklisted")
            self.log_message(f"Email blacklisted: {email}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to blacklist email: {str(e)}")
        
        
    def create_automation_tab(self):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Automation")
        
        main_frame = ttk.Frame(tab_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Product URL Configuration
        url_frame = ttk.LabelFrame(main_frame, text="Product Configuration", padding="10")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="Product URL:", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.product_url_var = tk.StringVar(value="localhost:8000/apple/iphone-17-pro/6.3-inch-display-256gb-deep-blue-unlocked")
        url_entry = ttk.Entry(url_frame, textvariable=self.product_url_var, font=('Arial', 9), width=80)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        
        validate_url_btn = ttk.Button(url_frame, text="Validate URL", 
                                     command=self.validate_product_url, style='Primary.TButton')
        validate_url_btn.grid(row=0, column=2, sticky=tk.W, pady=5)
        
        self.continuous_mode_var = tk.BooleanVar(value=True)
        continuous_check = ttk.Checkbutton(url_frame, text="Continuous Mode (Auto-restart processes)", 
                                          variable=self.continuous_mode_var)
        continuous_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Bright Data Proxy Settings
        proxy_frame = ttk.LabelFrame(main_frame, text="Bright Data Proxy Settings", padding="10")
        proxy_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        proxy_frame.columnconfigure(1, weight=1)
        
        self.use_proxy_var = tk.BooleanVar(value=False)
        proxy_check = ttk.Checkbutton(proxy_frame, text="Enable Bright Data Proxy (Different IP per process)", 
                                     variable=self.use_proxy_var, command=self.toggle_proxy_settings)
        proxy_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(proxy_frame, text="Zone ID:", font=('Arial', 9)).grid(
            row=1, column=0, sticky=tk.W, pady=2, padx=(20, 10))
        self.zone_id_label = ttk.Label(proxy_frame, text=f"{self.proxy.zone_id[:8]}...", 
                                      font=('Arial', 9), foreground='#6b7280')
        self.zone_id_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(proxy_frame, text="Username:", font=('Arial', 9)).grid(
            row=2, column=0, sticky=tk.W, pady=2, padx=(20, 10))
        self.username_label = ttk.Label(proxy_frame, text=self.proxy.username, 
                                       font=('Arial', 9), foreground='#6b7280')
        self.username_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(proxy_frame, text="Endpoint:", font=('Arial', 9)).grid(
            row=3, column=0, sticky=tk.W, pady=2, padx=(20, 10))
        self.endpoint_label = ttk.Label(proxy_frame, text=f"{self.proxy.endpoint}:{self.proxy.port}", 
                                       font=('Arial', 9), foreground='#6b7280')
        self.endpoint_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        self.test_proxy_btn = ttk.Button(proxy_frame, text="Test Proxy Connection", 
                                        command=self.test_proxy_connection, style='Primary.TButton',
                                        state='disabled')
        self.test_proxy_btn.grid(row=1, column=2, rowspan=3, sticky=tk.W, padx=(20, 0))
        
        self.proxy_status_label = ttk.Label(proxy_frame, text="Proxy disabled", 
                                           font=('Arial', 8), foreground='#6b7280')
        self.proxy_status_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0), padx=(20, 0))
        
        # Selection and Controls
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        
        selection_frame = ttk.LabelFrame(top_frame, text="Current Selection", padding="10")
        selection_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 7))
        
        self.card_selection_label = ttk.Label(selection_frame, text="No cards available", 
                                             font=('Arial', 9), foreground='#ef4444', wraplength=300)
        self.card_selection_label.pack(anchor=tk.W, pady=2)
        
        self.person_selection_label = ttk.Label(selection_frame, text="No pickup persons available",
                                               font=('Arial', 9), foreground='#ef4444', wraplength=300)
        self.person_selection_label.pack(anchor=tk.W, pady=2)
        
        self.location_selection_label = ttk.Label(selection_frame, text="No location settings available",
                                                 font=('Arial', 9), foreground='#ef4444', wraplength=300)
        self.location_selection_label.pack(anchor=tk.W, pady=2)
        
        refresh_btn = ttk.Button(selection_frame, text="Refresh Selection", 
                               command=self.refresh_selection, style='Primary.TButton')
        refresh_btn.pack(pady=(10, 0))
        
        control_frame = ttk.LabelFrame(top_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=(7, 0))
        
        test_btn = ttk.Button(control_frame, text="Test Selection", 
                             command=self.test_selection, style='Primary.TButton')
        test_btn.pack(fill=tk.X, pady=2)
        
        # Multi-Process Automation
        multi_frame = ttk.LabelFrame(main_frame, text="Multi-Process Automation", padding="10")
        multi_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        multi_frame.columnconfigure(0, weight=1)
        multi_frame.columnconfigure(1, weight=1)
        multi_frame.columnconfigure(2, weight=1)
        
        count_frame = ttk.Frame(multi_frame)
        count_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(count_frame, text="Number of Windows:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.process_count_var = tk.IntVar(value=2)
        self.process_count_spinbox = ttk.Spinbox(count_frame, from_=1, to=self.max_processes, 
                                               textvariable=self.process_count_var, width=10)
        self.process_count_spinbox.pack(anchor=tk.W, pady=2)
        
        controls_frame = ttk.Frame(multi_frame)
        controls_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(controls_frame, text="Multi-Process:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        self.start_multi_btn = ttk.Button(controls_frame, text="Start Multiple", 
                                         command=self.start_multi_automation, style='Warning.TButton')
        self.start_multi_btn.pack(fill=tk.X, pady=2)
        
        self.stop_all_btn = ttk.Button(controls_frame, text="Stop All Processes", 
                                      command=self.stop_all_processes, style='Danger.TButton',
                                      state='disabled')
        self.stop_all_btn.pack(fill=tk.X, pady=2)
        
        status_frame = ttk.Frame(multi_frame)
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(status_frame, text="Active Processes:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        self.process_status_label = ttk.Label(status_frame, text="No active processes", 
                                             font=('Arial', 8), foreground='#6b7280')
        self.process_status_label.pack(anchor=tk.W, pady=2)
        
        # Console Output
        console_frame = ttk.LabelFrame(main_frame, text="Automation Output", padding="10")
        console_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console_text = tk.Text(console_frame, height=15, wrap=tk.WORD,
                                   font=('Consolas', 9), bg='#1e1e1e', fg='#e5e7eb')
        
        console_scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        console_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        console_controls = ttk.Frame(console_frame)
        console_controls.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        clear_btn = ttk.Button(console_controls, text="Clear Console", command=self.clear_console)
        clear_btn.pack(side=tk.LEFT)

    def toggle_proxy_settings(self):
        if self.use_proxy_var.get():
            self.proxy.enable_proxy()
            self.test_proxy_btn.config(state='normal')
            self.proxy_status_label.config(text="Proxy enabled - Ready to use different IP per process", 
                                          foreground='#10b981')
            self.log_message("Bright Data proxy enabled")
        else:
            self.proxy.disable_proxy()
            self.test_proxy_btn.config(state='disabled')
            self.proxy_status_label.config(text="Proxy disabled", foreground='#6b7280')
            self.log_message("Bright Data proxy disabled")

    def test_proxy_connection(self):
        if not self.use_proxy_var.get():
            messagebox.showwarning("Warning", "Please enable proxy first")
            return
            
        self.log_message("Testing Bright Data proxy connection...")
        self.test_proxy_btn.config(state='disabled', text="Testing...")
        
        def test_thread():
            try:
                success, result = self.proxy.test_proxy(1)
                if success:
                    self.log_message(f"Proxy test successful! IP: {result}")
                    self.root.after(0, lambda: self.proxy_status_label.config(
                        text=f"Proxy working - Test IP: {result}", foreground='#10b981'))
                    self.root.after(0, lambda: messagebox.showinfo("Proxy Test", f"Connection successful!\nTest IP: {result}"))
                else:
                    self.log_message(f"Proxy test failed: {result}")
                    self.root.after(0, lambda: self.proxy_status_label.config(
                        text=f"Proxy test failed: {result}", foreground='#ef4444'))
                    self.root.after(0, lambda: messagebox.showerror("Proxy Test", f"Connection failed!\nError: {result}\n\nPlease check:\n1. Zone ID and Username in config.py\n2. Internet connection\n3. Bright Data account status"))
            except Exception as e:
                self.log_message(f"Proxy test error: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Proxy Test", f"Test error: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.test_proxy_btn.config(state='normal', text="Test Proxy Connection"))
        
        threading.Thread(target=test_thread, daemon=True).start()

    def validate_product_url(self):
        url = self.product_url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a product URL")
            return False
        self.log_message(f"Product URL set to: {url}")
        messagebox.showinfo("Success", "Product URL validated and set!")
        return True
        
    def start_multi_automation(self):
        try:
            
            count = self.process_count_var.get()
            product_url = self.product_url_var.get().strip()
            use_proxy = self.use_proxy_var.get()
            
            if not product_url:
                messagebox.showerror("Error", "Please enter a product URL")
                return
            
            card = self.db.get_all_cards()
            person = self.db.get_primary_pickup_person()
            settings = self.db.get_default_settings()
            
            if not card or not person or not settings:
                messagebox.showerror("Error", "Missing required data. Please check your selection.")
                return
            self.email_manager.cleanup_failed_processes()
            self.continuous_mode = self.continuous_mode_var.get()
            self._stopped = False
            
            self.start_multi_btn.config(state='disabled')
            self.stop_all_btn.config(state='normal')
            self.log_message(f"Starting {count} automation processes...")
            
            if self.continuous_mode:
                self.log_message("CONTINUOUS MODE ENABLED - Processes will auto-restart when completed")
            
            if use_proxy:
                self.log_message("BRIGHT DATA PROXY ENABLED - Each process will use different IP")
            else:
                self.log_message("Running without proxy - All processes use same IP")
            
            for i in range(count):
                if i > 0:
                    self.log_message(f"Starting process {i+1}/{count}...")
                    import time
                    time.sleep(2)
                
                automation = self.AppleAutomation(
                    card_data=card[0],
                    person_data=person,
                    settings_data=settings,
                    product_url=product_url,
                    use_proxy=use_proxy,
                    process_num=i+1
                )
                
                thread = threading.Thread(target=self.run_multi_automation_continuous, args=(automation, i+1))
                thread.daemon = True
                thread.start()
                
                self.active_processes.append(f"Process {i+1}")
            
            self.update_process_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start multi-automation: {str(e)}")
            self.reset_automation_ui()
    
    def run_multi_automation_continuous(self, automation, process_num):
        cycle_count = 0
        
        while not self._stopped and self.continuous_mode:
            try:
                cycle_count += 1
                proxy_info = " (WITH PROXY)" if self.use_proxy_var.get() else " (NO PROXY)"
                self.log_message(f"Process {process_num}: Starting cycle {cycle_count}{proxy_info}...")
                
                product_url = self.product_url_var.get().strip()
                automation.config.PRODUCT_URL = product_url
                automation.use_proxy = self.use_proxy_var.get()
                
                result = automation.run()
                
                if result:
                    self.log_message(f"Process {process_num}: Cycle {cycle_count} completed successfully!")
                else:
                    self.log_message(f"Process {process_num}: Cycle {cycle_count} failed")
                
                if self.continuous_mode and not self._stopped:
                    self.log_message(f"Process {process_num}: Waiting 10 seconds before next cycle...")
                    import time
                    time.sleep(10)
                else:
                    break
                    
            except Exception as e:
                self.log_message(f"Process {process_num}: Cycle {cycle_count} error - {str(e)}")
                if self.continuous_mode and not self._stopped:
                    self.log_message(f"Process {process_num}: Restarting in 15 seconds...")
                    import time
                    time.sleep(15)
                else:
                    break
        
        try:
            if f"Process {process_num}" in self.active_processes:
                self.active_processes.remove(f"Process {process_num}")
        except:
            pass
        
        self.root.after(0, self.update_process_status)
        self.log_message(f"Process {process_num}: Stopped after {cycle_count} cycles")
    
    def stop_all_processes(self):
        try:
            self.log_message("Stopping all automation processes...")
            self._stopped = True
            self.continuous_mode = False
            self.active_processes.clear()
            self.reset_automation_ui()
            self.log_message("All processes stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop automation: {str(e)}")
    
    def reset_automation_ui(self):
        self.start_multi_btn.config(state='normal')
        self.stop_all_btn.config(state='disabled')
        self.automation = None
        self.automation_thread = None
        self.active_processes.clear()
        self._stopped = False
        self.update_process_status()
    
    def update_process_status(self):
        if self.active_processes:
            status_text = f"Active: {len(self.active_processes)} processes"
            if self.continuous_mode:
                status_text += " (Continuous Mode)"
            if self.use_proxy_var.get():
                status_text += " (With Proxy)"
            status_text += "\n"
            status_text += ", ".join(self.active_processes[:3])
            if len(self.active_processes) > 3:
                status_text += f" and {len(self.active_processes) - 3} more..."
            self.process_status_label.config(text=status_text, foreground='#10b981')
        else:
            self.process_status_label.config(text="No active processes", foreground='#6b7280')
    
    def create_cards_tab(self):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Payment Cards")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        left_frame = ttk.LabelFrame(main_frame, text="Add New Payment Card", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_card_form(left_frame)
        
        right_frame = ttk.LabelFrame(main_frame, text="Saved Payment Cards", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_cards_list(right_frame)
        
    def create_card_form(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))
        
        self.card_vars = {}
        default_values = self.config.DEFAULT_VALUES
        
        fields = [
            ("Card Name:", "card_name_var", "Personal Card"),
            ("Card Number:", "card_number_var", default_values['credit_card']),
            ("Expiry:", "card_expiry_var", default_values['expiry_date']),
            ("CVC:", "card_cvc_var", default_values['cvc']),
            ("First Name:", "user_first_var", default_values['first_name']),
            ("Last Name:", "user_last_var", default_values['last_name']),
            ("Email:", "user_email_var", default_values['email']),
            ("Phone:", "user_phone_var", default_values['phone']),
            ("Bill First:", "billing_first_var", default_values['first_name']),
            ("Bill Last:", "billing_last_var", default_values['last_name']),
            ("Bill Street:", "billing_street_var", default_values['street_address']),
            ("Bill Postal:", "billing_postal_var", default_values['postal_code'])
        ]
        
        for i, (label, var_name, default_value) in enumerate(fields):
            ttk.Label(scrollable_frame, text=label, font=('Arial', 8)).grid(
                row=i, column=0, sticky=tk.W, pady=2, padx=(5, 5))
            
            var = tk.StringVar()
            if not self.db.get_all_cards() and default_value:
                var.set(default_value)
            self.card_vars[var_name] = var
            
            entry = ttk.Entry(scrollable_frame, textvariable=var, font=('Arial', 8), width=25)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 5))
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=15)
        
        copy_btn = ttk.Button(button_frame, text="Copy User to Bill", command=self.auto_fill_billing)
        copy_btn.pack(pady=3)
        
        add_btn = ttk.Button(button_frame, text="Add Card", command=self.add_card, style='Success.TButton')
        add_btn.pack(pady=3)
        
        canvas.configure(height=400)
        
    def create_cards_list(self, parent):
        refresh_btn = ttk.Button(parent, text="Refresh", command=self.load_cards)
        refresh_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.cards_listbox = tk.Listbox(list_frame, font=('Arial', 9))
        cards_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.cards_listbox.yview)
        self.cards_listbox.configure(yscrollcommand=cards_scrollbar.set)
        
        self.cards_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        cards_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        delete_btn = ttk.Button(parent, text="Delete Selected", 
                               command=self.delete_selected_card, style='Danger.TButton')
        delete_btn.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
    def create_persons_tab(self):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Pickup Persons")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        left_frame = ttk.LabelFrame(main_frame, text="Add New Pickup Person", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_person_form(left_frame)
        
        right_frame = ttk.LabelFrame(main_frame, text="Saved Pickup Persons", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_persons_list(right_frame)
        
    def create_person_form(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))
        
        explanation = ttk.Label(scrollable_frame, text="First person added becomes PRIMARY pickup person",
                               font=('Arial', 9), foreground='#2563eb', wraplength=250)
        explanation.pack(anchor=tk.W, pady=(5, 10), padx=5)
        
        self.person_vars = {}
        default_values = self.config.DEFAULT_VALUES
        
        fields = [
            ("Person Name:", "person_name_var", "Primary Person"),
            ("First Name:", "person_first_var", default_values['first_name']),
            ("Last Name:", "person_last_var", default_values['last_name']),
            ("Email:", "person_email_var", default_values['email']),
            ("Phone:", "person_phone_var", default_values['phone'])
        ]
        
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill=tk.X, padx=5)
        
        for i, (label, var_name, default_value) in enumerate(fields):
            ttk.Label(form_frame, text=label, font=('Arial', 9)).grid(
                row=i, column=0, sticky=tk.W, pady=3, padx=(0, 5))
            
            var = tk.StringVar()
            if not self.db.get_all_pickup_persons() and default_value:
                var.set(default_value)
            self.person_vars[var_name] = var
            
            entry = ttk.Entry(form_frame, textvariable=var, font=('Arial', 9), width=25)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3)
        
        form_frame.columnconfigure(1, weight=1)
        
        self.is_primary_person_var = tk.BooleanVar()
        if not self.db.get_all_pickup_persons():
            self.is_primary_person_var.set(True)
            
        primary_check = ttk.Checkbutton(form_frame, text="Set as primary", 
                                       variable=self.is_primary_person_var)
        primary_check.grid(row=len(fields), column=0, columnspan=2, sticky=tk.W, pady=5)
        
        add_btn = ttk.Button(form_frame, text="Add Person", 
                            command=self.add_person, style='Success.TButton')
        add_btn.grid(row=len(fields)+1, column=0, columnspan=2, pady=15)
        
        canvas.configure(height=300)
        
    def create_persons_list(self, parent):
        refresh_btn = ttk.Button(parent, text="Refresh", command=self.load_persons)
        refresh_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.persons_listbox = tk.Listbox(list_frame, font=('Arial', 9))
        persons_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.persons_listbox.yview)
        self.persons_listbox.configure(yscrollcommand=persons_scrollbar.set)
        
        self.persons_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        persons_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        delete_btn = ttk.Button(parent, text="Delete Selected", 
                               command=self.delete_selected_person, style='Danger.TButton')
        delete_btn.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
    def create_settings_tab(self):
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Settings")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        left_frame = ttk.LabelFrame(main_frame, text="Add Location Settings", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_settings_form(left_frame)
        
        right_frame = ttk.LabelFrame(main_frame, text="Saved Location Settings", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_settings_list(right_frame)
        
    def create_settings_form(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))
        
        self.settings_vars = {}
        default_values = self.config.DEFAULT_VALUES
        
        ttk.Label(scrollable_frame, text="Zip Codes (one per line):", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(5, 2), padx=5)
        
        self.zip_codes_text = tk.Text(scrollable_frame, height=5, width=25, font=('Arial', 9))
        self.zip_codes_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10), padx=5)
        
        if not self.db.get_all_settings():
            self.zip_codes_text.insert('1.0', default_values['zip_code'])
        
        fields = [
            ("Street Address:", "settings_street_var", default_values['street_address']),
            ("Postal Code:", "settings_postal_var", default_values['postal_code'])
        ]
        
        start_row = 2
        for i, (label, var_name, default_value) in enumerate(fields):
            ttk.Label(scrollable_frame, text=label, font=('Arial', 9)).grid(
                row=start_row + i, column=0, sticky=tk.W, pady=5, padx=(5, 5))
            
            var = tk.StringVar()
            if not self.db.get_all_settings() and default_value:
                var.set(default_value)
            self.settings_vars[var_name] = var
            
            entry = ttk.Entry(scrollable_frame, textvariable=var, font=('Arial', 9), width=25)
            entry.grid(row=start_row + i, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        self.is_default_var = tk.BooleanVar()
        if not self.db.get_all_settings():
            self.is_default_var.set(True)
            
        default_check = ttk.Checkbutton(scrollable_frame, text="Set as default location", 
                                       variable=self.is_default_var)
        default_check.grid(row=start_row + len(fields), column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        add_btn = ttk.Button(scrollable_frame, text="Add Location", 
                            command=self.add_settings, style='Success.TButton')
        add_btn.grid(row=start_row + len(fields) + 1, column=0, columnspan=2, pady=15)
        
        canvas.configure(height=300)
        
    def create_settings_list(self, parent):
        refresh_btn = ttk.Button(parent, text="Refresh", command=self.load_settings)
        refresh_btn.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.settings_listbox = tk.Listbox(list_frame, font=('Arial', 9))
        settings_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.settings_listbox.yview)
        self.settings_listbox.configure(yscrollcommand=settings_scrollbar.set)
        
        self.settings_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        settings_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        delete_btn = ttk.Button(parent, text="Delete Selected", 
                               command=self.delete_selected_settings, style='Danger.TButton')
        delete_btn.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))

    def auto_fill_billing(self):
        try:
            self.card_vars['billing_first_var'].set(self.card_vars['user_first_var'].get())
            self.card_vars['billing_last_var'].set(self.card_vars['user_last_var'].get())
            
            settings = self.db.get_default_settings()
            if settings:
                self.card_vars['billing_street_var'].set(settings['street_address'])
                self.card_vars['billing_postal_var'].set(settings['postal_code'])
            
            messagebox.showinfo("Success", "Billing info copied!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {str(e)}")
    
    def add_card(self):
        try:
            required_fields = [
                'card_name_var', 'card_number_var', 'card_expiry_var', 'card_cvc_var',
                'user_first_var', 'user_last_var', 'user_email_var', 'user_phone_var',
                'billing_first_var', 'billing_last_var', 'billing_street_var', 'billing_postal_var'
            ]
            
            for field in required_fields:
                if not self.card_vars[field].get().strip():
                    field_name = field.replace('_var', '').replace('_', ' ').title()
                    messagebox.showerror("Error", f"Please fill: {field_name}")
                    return
            
            card_number = ''.join(c for c in self.card_vars['card_number_var'].get() if c.isdigit())
            if len(card_number) < 13 or len(card_number) > 19:
                messagebox.showerror("Error", "Invalid card number")
                return
            
            expiry = self.card_vars['card_expiry_var'].get()
            if len(expiry) != 5 or expiry[2] != '/' or not expiry[:2].isdigit() or not expiry[3:].isdigit():
                messagebox.showerror("Error", "Expiry must be MM/YY")
                return
            
            cvc = self.card_vars['card_cvc_var'].get()
            if not cvc.isdigit() or len(cvc) < 3 or len(cvc) > 4:
                messagebox.showerror("Error", "CVC must be 3-4 digits")
                return
            
            email = self.card_vars['user_email_var'].get().strip()
            if '@' not in email or '.' not in email.split('@')[1]:
                messagebox.showerror("Error", "Invalid email")
                return
            
            phone = self.card_vars['user_phone_var'].get().strip()
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if len(clean_phone) < 10:
                messagebox.showerror("Error", "Phone needs 10+ digits")
                return
            
            user_info = {
                'first_name': self.card_vars['user_first_var'].get().strip(),
                'last_name': self.card_vars['user_last_var'].get().strip(),
                'email': email,
                'phone': phone
            }
            
            billing_info = {
                'first_name': self.card_vars['billing_first_var'].get().strip(),
                'last_name': self.card_vars['billing_last_var'].get().strip(),
                'street_address': self.card_vars['billing_street_var'].get().strip(),
                'postal_code': self.card_vars['billing_postal_var'].get().strip()
            }
            
            self.db.add_card(
                name=self.card_vars['card_name_var'].get().strip(),
                card_number=card_number,
                expiry_date=expiry,
                cvc=cvc,
                billing_info=billing_info,
                user_info=user_info
            )
            
            for var in self.card_vars.values():
                var.set("")
            
            self.load_cards()
            self.update_stats()
            self.refresh_selection()
            
            messagebox.showinfo("Success", "Card added!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add card: {str(e)}")
    
    def add_person(self):
        try:
            required_fields = ['person_name_var', 'person_first_var', 'person_last_var', 
                             'person_email_var', 'person_phone_var']
            
            for field in required_fields:
                if not self.person_vars[field].get().strip():
                    messagebox.showerror("Error", "Please fill all fields")
                    return
            
            email = self.person_vars['person_email_var'].get().strip()
            if '@' not in email or '.' not in email.split('@')[1]:
                messagebox.showerror("Error", "Invalid email")
                return
            
            phone = self.person_vars['person_phone_var'].get().strip()
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if len(clean_phone) < 10:
                messagebox.showerror("Error", "Phone needs 10+ digits")
                return
            
            self.db.add_pickup_person(
                name=self.person_vars['person_name_var'].get().strip(),
                first_name=self.person_vars['person_first_var'].get().strip(),
                last_name=self.person_vars['person_last_var'].get().strip(),
                email=email,
                phone=phone,
                is_primary=self.is_primary_person_var.get()
            )
            
            for var in self.person_vars.values():
                var.set("")
            self.is_primary_person_var.set(False)
            
            self.load_persons()
            self.update_stats()
            self.refresh_selection()
            
            messagebox.showinfo("Success", "Person added!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add person: {str(e)}")
    
    def add_settings(self):
        try:
            zip_codes_text = self.zip_codes_text.get('1.0', tk.END).strip()
            if not zip_codes_text:
                messagebox.showerror("Error", "Please enter at least one zip code")
                return
            
            zip_codes = [code.strip() for code in zip_codes_text.split('\n') if code.strip()]
            if not zip_codes:
                messagebox.showerror("Error", "Please enter valid zip codes")
                return
            
            required_fields = ['settings_street_var', 'settings_postal_var']
            
            for field in required_fields:
                if not self.settings_vars[field].get().strip():
                    messagebox.showerror("Error", "Please fill all fields")
                    return
            
            for zip_code in zip_codes:
                self.db.add_settings(
                    zip_code=zip_code,
                    street_address=self.settings_vars['settings_street_var'].get().strip(),
                    postal_code=self.settings_vars['settings_postal_var'].get().strip(),
                    is_default=self.is_default_var.get() and zip_code == zip_codes[0]
                )
            
            self.zip_codes_text.delete('1.0', tk.END)
            for var in self.settings_vars.values():
                var.set("")
            self.is_default_var.set(False)
            
            self.load_settings()
            self.update_stats()
            self.refresh_selection()
            
            messagebox.showinfo("Success", f"Added {len(zip_codes)} location settings!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add settings: {str(e)}")

    def load_data(self):
        self.load_cards()
        self.load_persons()
        self.load_settings()
        self.refresh_selection()

    def delete_selected_card(self):
        try:
            selection = self.cards_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a card to delete")
                return
            
            if messagebox.askyesno("Confirm", "Delete selected card?"):
                index = selection[0]
                cards = self.db.get_all_cards()
                if index < len(cards):
                    self.db.delete_card(cards[index]['id'])
                    self.load_cards()
                    self.update_stats()
                    self.refresh_selection()
                    messagebox.showinfo("Success", "Card deleted!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete card: {str(e)}")
    
    def delete_selected_person(self):
        try:
            selection = self.persons_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a person to delete")
                return
            
            if messagebox.askyesno("Confirm", "Delete selected person?"):
                index = selection[0]
                persons = self.db.get_all_pickup_persons()
                if index < len(persons):
                    self.db.delete_pickup_person(persons[index]['id'])
                    self.load_persons()
                    self.update_stats()
                    self.refresh_selection()
                    messagebox.showinfo("Success", "Person deleted!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete person: {str(e)}")
    
    def delete_selected_settings(self):
        try:
            selection = self.settings_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select settings to delete")
                return
            
            if messagebox.askyesno("Confirm", "Delete selected settings?"):
                index = selection[0]
                settings = self.db.get_all_settings()
                if index < len(settings):
                    self.db.delete_settings(settings[index]['id'])
                    self.load_settings()
                    self.update_stats()
                    self.refresh_selection()
                    messagebox.showinfo("Success", "Settings deleted!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete settings: {str(e)}")
    
    def load_cards(self):
        try:
            self.cards_listbox.delete(0, tk.END)
            cards = self.db.get_all_cards()
            for card in cards:
                display_text = f"{card['name']} - *{card['card_number'][-4:]}"
                self.cards_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading cards: {e}")
    
    def load_persons(self):
        try:
            self.persons_listbox.delete(0, tk.END)
            persons = self.db.get_all_pickup_persons()
            for person in persons:
                primary_text = " (PRIMARY)" if person['is_primary'] else ""
                display_text = f"{person['name']} - {person['first_name']} {person['last_name']}{primary_text}"
                self.persons_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading persons: {e}")

    def load_settings(self):
        try:
            self.settings_listbox.delete(0, tk.END)
            settings = self.db.get_all_settings()
            grouped_settings = {}
            
            for setting in settings:
                key = f"{setting['street_address']} - {setting['postal_code']}"
                if key not in grouped_settings:
                    grouped_settings[key] = []
                grouped_settings[key].append(setting)
            
            for key, group in grouped_settings.items():
                zip_codes = [s['zip_code'] for s in group]
                default_text = " (DEFAULT)" if any(s['is_default'] for s in group) else ""
                display_text = f"Zips: {', '.join(zip_codes)} - {key}{default_text}"
                self.settings_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def update_stats(self):
        try:
            for widget in self.stats_frame.winfo_children():
                widget.destroy()
            
            cards_count = len(self.db.get_all_cards())
            persons_count = len(self.db.get_all_pickup_persons())
            settings_count = len(self.db.get_all_settings())
            
            stats_text = f"Cards: {cards_count} | Persons: {persons_count} | Locations: {settings_count}"
            stats_label = ttk.Label(self.stats_frame, text=stats_text, font=('Arial', 9))
            stats_label.pack()
            
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def refresh_selection(self):
        try:
            cards = self.db.get_all_cards()
            if cards:
                card = cards[0]
                card_text = f"✓ Card: {card['name']} (*{card['card_number'][-4:]})"
                self.card_selection_label.config(text=card_text, foreground='#10b981')
            else:
                self.card_selection_label.config(text="No cards available", foreground='#ef4444')
            
            primary_person = self.db.get_primary_pickup_person()
            if primary_person:
                person_text = f"✓ Person: {primary_person['name']} ({primary_person['first_name']} {primary_person['last_name']})"
                self.person_selection_label.config(text=person_text, foreground='#10b981')
            else:
                self.person_selection_label.config(text="No pickup persons available", foreground='#ef4444')
            
            default_settings = self.db.get_default_settings()
            if default_settings:
                location_text = f"✓ Location: {default_settings['zip_code']} - {default_settings['street_address']}"
                self.location_selection_label.config(text=location_text, foreground='#10b981')
            else:
                self.location_selection_label.config(text="No location settings available", foreground='#ef4444')
                
        except Exception as e:
            print(f"Error refreshing selection: {e}")
    
    def test_selection(self):
        try:
            card = self.db.get_all_cards()
            person = self.db.get_primary_pickup_person()
            settings = self.db.get_default_settings()
            
            if not card:
                messagebox.showerror("Error", "No payment cards available")
                return
            if not person:
                messagebox.showerror("Error", "No pickup person available")
                return
            if not settings:
                messagebox.showerror("Error", "No location settings available")
                return
            
            proxy_status = "WITH PROXY" if self.use_proxy_var.get() else "WITHOUT PROXY"
            
            test_message = f"""Selection Test Results:
            
✓ Payment Card: {card[0]['name']}
✓ Pickup Person: {person['name']} ({person['first_name']} {person['last_name']})
✓ Location: {settings['zip_code']} - {settings['street_address']}
✓ Proxy Status: {proxy_status}

All required data is available for automation!"""
            
            messagebox.showinfo("Test Results", test_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Test failed: {str(e)}")
    
    def log_message(self, message):
        try:
            self.console_text.insert(tk.END, f"{message}\n")
            self.console_text.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Logging error: {e}")
    
    def clear_console(self):
        self.console_text.delete(1.0, tk.END)
    
    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred: {str(e)}")


def main():
    try:
        app = CleanModernGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")


if __name__ == "__main__":
    main()