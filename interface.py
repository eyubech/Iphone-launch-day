"""
Clean Modern GUI - Complete Working Version with Scrollable Forms
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from apple_automation import AppleAutomation
from config import Config
from database import DatabaseManager


class CleanModernGUI:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.root = tk.Tk()
        self.automation = None
        self.automation_thread = None
        
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.load_data()
        
    def setup_window(self):
        """Configure main window"""
        self.root.title("Apple iPhone Automation Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f8f9fa')
        self.root.resizable(True, True)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def setup_styles(self):
        """Configure styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Success.TButton',
                       font=('Arial', 9, 'bold'),
                       foreground='white',
                       background='#10b981')
        
        style.configure('Primary.TButton',
                       font=('Arial', 9, 'bold'),
                       foreground='white', 
                       background='#2563eb')
        
        style.configure('Danger.TButton',
                       font=('Arial', 9),
                       foreground='white',
                       background='#ef4444')
        
    def create_widgets(self):
        """Create main interface"""
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text="iPhone Automation Pro", 
                               font=('Arial', 18, 'bold'), foreground='#2563eb')
        title_label.pack(side=tk.LEFT)
        
        # Stats
        self.stats_frame = ttk.Frame(header_frame)
        self.stats_frame.pack(side=tk.RIGHT)
        
        # Create notebook
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create tabs
        self.create_automation_tab()
        self.create_cards_tab()
        self.create_persons_tab()
        self.create_settings_tab()
        
        self.update_stats()
        
    def create_automation_tab(self):
        """Create automation tab"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Automation")
        
        main_frame = ttk.Frame(tab_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top section
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        
        # Selection display
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
        
        # Controls
        control_frame = ttk.LabelFrame(top_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=(7, 0))
        
        test_btn = ttk.Button(control_frame, text="Test Selection", 
                             command=self.test_selection, style='Primary.TButton')
        test_btn.pack(fill=tk.X, pady=2)
        
        self.start_btn = ttk.Button(control_frame, text="Start Automation", 
                                   command=self.start_automation, style='Success.TButton')
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_automation, style='Danger.TButton',
                                  state='disabled')
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        # Console output
        console_frame = ttk.LabelFrame(main_frame, text="Automation Output", padding="10")
        console_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
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
        
    def create_cards_tab(self):
        """Create cards tab"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Payment Cards")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # Left - Add card form
        left_frame = ttk.LabelFrame(main_frame, text="Add New Payment Card", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_card_form(left_frame)
        
        # Right - Cards list
        right_frame = ttk.LabelFrame(main_frame, text="Saved Payment Cards", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_cards_list(right_frame)
        
    def create_card_form(self, parent):
        """Create card form with scrolling capability"""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas for smooth scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Now create the form content in the scrollable frame
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
        
        # Button frame at the bottom
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=15)
        
        copy_btn = ttk.Button(button_frame, text="Copy User to Bill", 
                             command=self.auto_fill_billing)
        copy_btn.pack(pady=3)
        
        add_btn = ttk.Button(button_frame, text="Add Card", 
                            command=self.add_card, style='Success.TButton')
        add_btn.pack(pady=3)
        
        # Set minimum canvas height to ensure scrolling works properly
        canvas.configure(height=400)
        
    def create_cards_list(self, parent):
        """Create cards list"""
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
        """Create persons tab"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Pickup Persons")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # Left - Add person form
        left_frame = ttk.LabelFrame(main_frame, text="Add New Pickup Person", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_person_form(left_frame)
        
        # Right - Persons list
        right_frame = ttk.LabelFrame(main_frame, text="Saved Pickup Persons", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_persons_list(right_frame)
        
    def create_person_form(self, parent):
        """Create person form with scrolling capability"""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas for smooth scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Now create the form content in the scrollable frame
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
        
        # Set minimum canvas height
        canvas.configure(height=300)
        
    def create_persons_list(self, parent):
        """Create persons list"""
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
        """Create settings tab"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Settings")
        
        main_frame = ttk.Frame(tab_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # Left - Add settings form
        left_frame = ttk.LabelFrame(main_frame, text="Add Location Settings", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.create_settings_form(left_frame)
        
        # Right - Settings list
        right_frame = ttk.LabelFrame(main_frame, text="Saved Location Settings", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.create_settings_list(right_frame)
        
    def create_settings_form(self, parent):
        """Create settings form with scrolling capability"""
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas for smooth scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Now create the form content in the scrollable frame
        self.settings_vars = {}
        default_values = self.config.DEFAULT_VALUES
        
        fields = [
            ("Zip Code:", "settings_zip_var", default_values['zip_code']),
            ("Street Address:", "settings_street_var", default_values['street_address']),
            ("Postal Code:", "settings_postal_var", default_values['postal_code'])
        ]
        
        for i, (label, var_name, default_value) in enumerate(fields):
            ttk.Label(scrollable_frame, text=label, font=('Arial', 9)).grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(5, 5))
            
            var = tk.StringVar()
            if not self.db.get_all_settings() and default_value:
                var.set(default_value)
            self.settings_vars[var_name] = var
            
            entry = ttk.Entry(scrollable_frame, textvariable=var, font=('Arial', 9), width=25)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 5))
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        self.is_default_var = tk.BooleanVar()
        if not self.db.get_all_settings():
            self.is_default_var.set(True)
            
        default_check = ttk.Checkbutton(scrollable_frame, text="Set as default location", 
                                       variable=self.is_default_var)
        default_check.grid(row=len(fields), column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        add_btn = ttk.Button(scrollable_frame, text="Add Location", 
                            command=self.add_settings, style='Success.TButton')
        add_btn.grid(row=len(fields)+1, column=0, columnspan=2, pady=15)
        
        # Set minimum canvas height
        canvas.configure(height=200)
        
    def create_settings_list(self, parent):
        """Create settings list"""
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
        
    # Database operations
    def auto_fill_billing(self):
        """Auto-fill billing from user info"""
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
        """Add new card"""
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
        """Add new person"""
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
        """Add new settings"""
        try:
            required_fields = ['settings_zip_var', 'settings_street_var', 'settings_postal_var']
            
            for field in required_fields:
                if not self.settings_vars[field].get().strip():
                    messagebox.showerror("Error", "Please fill all fields")
                    return
            
            self.db.add_settings(
                zip_code=self.settings_vars['settings_zip_var'].get().strip(),
                street_address=self.settings_vars['settings_street_var'].get().strip(),
                postal_code=self.settings_vars['settings_postal_var'].get().strip(),
                is_default=self.is_default_var.get()
            )
            
            for var in self.settings_vars.values():
                var.set("")
            self.is_default_var.set(False)
            
            self.load_settings()
            self.update_stats()
            self.refresh_selection()
            
            messagebox.showinfo("Success", "Settings added!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add settings: {str(e)}")
    
    def delete_selected_card(self):
        """Delete selected card"""
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
        """Delete selected person"""
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
        """Delete selected settings"""
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
    
    def load_data(self):
        """Load all data"""
        self.load_cards()
        self.load_persons()
        self.load_settings()
        self.refresh_selection()
    
    def load_cards(self):
        """Load cards into listbox"""
        try:
            self.cards_listbox.delete(0, tk.END)
            cards = self.db.get_all_cards()
            for card in cards:
                display_text = f"{card['name']} - *{card['card_number'][-4:]}"
                self.cards_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading cards: {e}")
    
    def load_persons(self):
        """Load persons into listbox"""
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
        """Load settings into listbox"""
        try:
            self.settings_listbox.delete(0, tk.END)
            settings = self.db.get_all_settings()
            for setting in settings:
                default_text = " (DEFAULT)" if setting['is_default'] else ""
                display_text = f"{setting['zip_code']} - {setting['street_address']}{default_text}"
                self.settings_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def update_stats(self):
        """Update statistics display"""
        try:
            # Clear existing stats
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
        """Refresh current selection display"""
        try:
            # Check for default card
            cards = self.db.get_all_cards()
            if cards:
                card = cards[0]  # First card as default
                card_text = f"✓ Card: {card['name']} (*{card['card_number'][-4:]})"
                self.card_selection_label.config(text=card_text, foreground='#10b981')
            else:
                self.card_selection_label.config(text="No cards available", foreground='#ef4444')
            
            # Check for primary person
            primary_person = self.db.get_primary_pickup_person()
            if primary_person:
                person_text = f"✓ Person: {primary_person['name']} ({primary_person['first_name']} {primary_person['last_name']})"
                self.person_selection_label.config(text=person_text, foreground='#10b981')
            else:
                self.person_selection_label.config(text="No pickup persons available", foreground='#ef4444')
            
            # Check for default location
            default_settings = self.db.get_default_settings()
            if default_settings:
                location_text = f"✓ Location: {default_settings['zip_code']} - {default_settings['street_address']}"
                self.location_selection_label.config(text=location_text, foreground='#10b981')
            else:
                self.location_selection_label.config(text="No location settings available", foreground='#ef4444')
                
        except Exception as e:
            print(f"Error refreshing selection: {e}")
    
    def test_selection(self):
        """Test current selection"""
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
            
            test_message = f"""Selection Test Results:
            
✓ Payment Card: {card[0]['name']}
✓ Pickup Person: {person['name']} ({person['first_name']} {person['last_name']})
✓ Location: {settings['zip_code']} - {settings['street_address']}

All required data is available for automation!"""
            
            messagebox.showinfo("Test Results", test_message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Test failed: {str(e)}")
    
    def start_automation(self):
        """Start automation process"""
        try:
            # Validate selection
            card = self.db.get_all_cards()
            person = self.db.get_primary_pickup_person()
            settings = self.db.get_default_settings()
            
            if not card or not person or not settings:
                messagebox.showerror("Error", "Missing required data. Please check your selection.")
                return
            
            # Update UI
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.log_message("Starting automation...")
            
            # Initialize automation
            self.automation = AppleAutomation(
                card_data=card[0],
                person_data=person,
                settings_data=settings
            )
            
            # Start automation in separate thread
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start automation: {str(e)}")
            self.reset_automation_ui()
    
    def run_automation(self):
        """Run automation in background thread"""
        try:
            self.automation.run()
        except Exception as e:
            self.log_message(f"Automation error: {str(e)}")
        finally:
            self.root.after(0, self.reset_automation_ui)
    
    def stop_automation(self):
        """Stop automation process"""
        try:
            if self.automation:
                self.automation.stop()
                self.log_message("Stopping automation...")
            self.reset_automation_ui()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop automation: {str(e)}")
    
    def reset_automation_ui(self):
        """Reset automation UI state"""
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.automation = None
        self.automation_thread = None
    
    def log_message(self, message):
        """Log message to console"""
        try:
            self.console_text.insert(tk.END, f"{message}\n")
            self.console_text.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Logging error: {e}")
    
    def clear_console(self):
        """Clear console output"""
        self.console_text.delete(1.0, tk.END)
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred: {str(e)}")


def main():
    """Main application entry point"""
    try:
        app = CleanModernGUI()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")


if __name__ == "__main__":
    main()