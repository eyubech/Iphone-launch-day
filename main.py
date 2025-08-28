import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import queue
from datetime import datetime
from iphone_automation import IPhoneAutomation
from config_manager import ConfigManager

class IPhoneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iPhone Automation Tool Pro")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.automation = None
        self.log_queue = queue.Queue()
        self.is_running = False
        
        # Style configuration
        self.setup_styles()
        
        # Create GUI
        self.create_gui()
        
        # Start log update timer
        self.root.after(100, self.update_logs)
    
    def setup_styles(self):
        """Configure modern styles for the GUI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('Action.TButton',
                       background='#007AFF',
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       padding=(20, 10))
        
        style.configure('Stop.TButton',
                       background='#FF3B30',
                       foreground='white',
                       font=('Helvetica', 10, 'bold'),
                       padding=(20, 10))
        
        style.configure('Secondary.TButton',
                       background='#34C759',
                       foreground='white',
                       font=('Helvetica', 9),
                       padding=(15, 8))
    
    def create_gui(self):
        """Create the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = tk.Label(main_frame, text="iPhone Automation Tool Pro", 
                              font=('Helvetica', 18, 'bold'),
                              bg='#f0f0f0', fg='#333')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Configuration
        self.create_config_panel(main_frame)
        
        # Right panel - Control and logs
        self.create_control_panel(main_frame)
    
    def create_config_panel(self, parent):
        """Create the configuration panel"""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="15")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # iPhone Model Selection
        model_frame = ttk.LabelFrame(config_frame, text="iPhone Model", padding="10")
        model_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.model_var = tk.StringVar(value="16")
        models = ["14", "15", "16"]
        for i, model in enumerate(models):
            ttk.Radiobutton(model_frame, text=f"iPhone {model}", 
                           variable=self.model_var, value=model).grid(row=0, column=i, padx=10)
        
        # Variant Selection
        variant_frame = ttk.LabelFrame(config_frame, text="Variant", padding="10")
        variant_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.variant_var = tk.StringVar(value="Pro")
        variants = ["Standard", "Plus", "Pro", "Pro Max"]
        for i, variant in enumerate(variants):
            ttk.Radiobutton(variant_frame, text=variant, 
                           variable=self.variant_var, value=variant).grid(row=i//2, column=i%2, padx=10, sticky=tk.W)
        
        # Configuration Mode
        mode_frame = ttk.LabelFrame(config_frame, text="Configuration Mode", padding="10")
        mode_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="manual")
        ttk.Radiobutton(mode_frame, text="Manual Selection", 
                       variable=self.mode_var, value="manual",
                       command=self.toggle_mode).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Try All Combinations", 
                       variable=self.mode_var, value="auto",
                       command=self.toggle_mode).grid(row=1, column=0, sticky=tk.W)
        
        # Manual selection frame
        self.manual_frame = ttk.LabelFrame(config_frame, text="Manual Options", padding="10")
        self.manual_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Color selection
        ttk.Label(self.manual_frame, text="Color:").grid(row=0, column=0, sticky=tk.W)
        self.color_var = tk.StringVar(value="1")
        color_combo = ttk.Combobox(self.manual_frame, textvariable=self.color_var, 
                                  values=["1", "2", "3"], width=5)
        color_combo.grid(row=0, column=1, padx=(10, 0))
        
        # Storage selection
        ttk.Label(self.manual_frame, text="Storage:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.storage_var = tk.StringVar(value="1")
        storage_combo = ttk.Combobox(self.manual_frame, textvariable=self.storage_var,
                                   values=["1", "2", "3"], width=5)
        storage_combo.grid(row=1, column=1, padx=(10, 0), pady=(10, 0))
        
        # Pieces
        ttk.Label(self.manual_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.pieces_var = tk.StringVar(value="1")
        pieces_spin = ttk.Spinbox(self.manual_frame, from_=1, to=10, 
                                 textvariable=self.pieces_var, width=5)
        pieces_spin.grid(row=2, column=1, padx=(10, 0), pady=(10, 0))
        
        # JSON file operations
        json_frame = ttk.LabelFrame(config_frame, text="JSON Configuration", padding="10")
        json_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(json_frame, text="Load JSON", 
                  command=self.load_json, style='Secondary.TButton').grid(row=0, column=0, padx=(0, 10))
        ttk.Button(json_frame, text="Save Config", 
                  command=self.save_config, style='Secondary.TButton').grid(row=0, column=1)
    
    def create_control_panel(self, parent):
        """Create the control and log panel"""
        control_frame = ttk.LabelFrame(parent, text="Control & Logs", padding="15")
        control_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        control_frame.rowconfigure(1, weight=1)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Automation", 
                                   command=self.start_automation, style='Action.TButton')
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", 
                                  command=self.stop_automation, style='Stop.TButton', state='disabled')
        self.stop_btn.grid(row=0, column=1)
        
        # Status indicator
        self.status_frame = ttk.Frame(button_frame)
        self.status_frame.grid(row=0, column=2, padx=(20, 0))
        
        self.status_label = tk.Label(self.status_frame, text="● Ready", 
                                   fg='#34C759', font=('Helvetica', 10, 'bold'))
        self.status_label.grid(row=0, column=0)
        
        # Log display
        log_frame = ttk.LabelFrame(control_frame, text="Activity Log", padding="10")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=50,
                                                 font=('Consolas', 9),
                                                 bg='#1e1e1e', fg='#ffffff',
                                                 insertbackground='white')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear logs button
        ttk.Button(log_frame, text="Clear Logs", 
                  command=self.clear_logs).grid(row=1, column=0, pady=(10, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def toggle_mode(self):
        """Toggle between manual and auto mode"""
        if self.mode_var.get() == "manual":
            for child in self.manual_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.manual_frame.winfo_children():
                if isinstance(child, (ttk.Combobox, ttk.Spinbox)):
                    child.configure(state='disabled')
    
    def log_message(self, message, level="INFO"):
        """Add message to log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {
            "INFO": "#ffffff",
            "SUCCESS": "#34C759",
            "WARNING": "#FF9500", 
            "ERROR": "#FF3B30"
        }.get(level, "#ffffff")
        
        self.log_queue.put((f"[{timestamp}] {message}", color))
    
    def update_logs(self):
        """Update log display from queue"""
        try:
            while True:
                message, color = self.log_queue.get_nowait()
                self.log_text.configure(state='normal')
                self.log_text.insert(tk.END, message + "\n")
                
                # Color the last line
                line_start = self.log_text.index("end-2l")
                line_end = self.log_text.index("end-1l")
                self.log_text.tag_add("colored", line_start, line_end)
                self.log_text.tag_configure("colored", foreground=color)
                
                self.log_text.configure(state='disabled')
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_logs)
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def update_status(self, status, color):
        """Update status indicator"""
        self.status_label.configure(text=f"● {status}", fg=color)
    
    def start_automation(self):
        """Start the automation process"""
        if self.is_running:
            return
            
        # Validate configuration
        config = self.get_current_config()
        if not config:
            messagebox.showerror("Error", "Please configure all required settings")
            return
        
        self.is_running = True
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.progress.start()
        self.update_status("Running", "#FF9500")
        
        # Start automation in separate thread
        self.automation_thread = threading.Thread(target=self.run_automation, args=(config,))
        self.automation_thread.daemon = True
        self.automation_thread.start()
    
    def stop_automation(self):
        """Stop the automation process"""
        if self.automation and hasattr(self.automation, 'stop'):
            self.automation.stop()
        
        self.is_running = False
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.progress.stop()
        self.update_status("Stopped", "#FF3B30")
        self.log_message("Automation stopped by user", "WARNING")
    
    def run_automation(self, config):
        """Run the automation process"""
        try:
            self.log_message("Starting iPhone automation...", "INFO")
            
            self.automation = IPhoneAutomation(self.log_message)
            success = self.automation.process_configurations(config)
            
            if success:
                self.log_message("Automation completed successfully!", "SUCCESS")
                self.update_status("Completed", "#34C759")
            else:
                self.log_message("Automation completed with errors", "WARNING")
                self.update_status("Warning", "#FF9500")
                
        except Exception as e:
            self.log_message(f"Automation failed: {str(e)}", "ERROR")
            self.update_status("Error", "#FF3B30")
        finally:
            self.is_running = False
            self.start_btn.configure(state='normal')
            self.stop_btn.configure(state='disabled')
            self.progress.stop()
    
    def get_current_config(self):
        """Get current configuration from GUI"""
        try:
            model = self.model_var.get()
            variant = self.variant_var.get()
            mode = self.mode_var.get()
            
            if mode == "manual":
                return [{
                    "version": f"{model} {variant}",
                    "color": int(self.color_var.get()),
                    "storage": int(self.storage_var.get()),
                    "pieces": int(self.pieces_var.get())
                }]
            else:
                # Generate all combinations
                configs = []
                for color in [1, 2, 3]:
                    for storage in [1, 2, 3]:
                        configs.append({
                            "version": f"{model} {variant}",
                            "color": color,
                            "storage": storage,
                            "pieces": 1
                        })
                return configs
                
        except ValueError:
            return None
    
    def load_json(self):
        """Load configuration from JSON file"""
        filename = filedialog.askopenfilename(
            title="Select JSON Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as file:
                    data = json.load(file)
                self.log_message(f"Loaded configuration from {filename}", "SUCCESS")
                # You could set GUI values based on loaded data here
            except Exception as e:
                self.log_message(f"Failed to load JSON: {str(e)}", "ERROR")
    
    def save_config(self):
        """Save current configuration to JSON file"""
        config = self.get_current_config()
        if not config:
            messagebox.showerror("Error", "No valid configuration to save")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as file:
                    json.dump(config, file, indent=2)
                self.log_message(f"Configuration saved to {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to save configuration: {str(e)}", "ERROR")

def main():
    root = tk.Tk()
    app = IPhoneGUI(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()