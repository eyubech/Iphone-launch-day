"""
Apple iPhone automation script - Main entry point with Clean Modern GUI
"""

import sys
import tkinter as tk
from tkinter import messagebox


def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []
    
    try:
        import selenium
    except ImportError:
        missing_deps.append("selenium")
    
    try:
        import cryptography
    except ImportError:
        missing_deps.append("cryptography")
    
    if missing_deps:
        deps_str = ", ".join(missing_deps)
        error_msg = f"""
Missing required dependencies: {deps_str}

Please install them using:
pip install {" ".join(missing_deps)}

Or install all requirements:
pip install -r requirements.txt
        """
        print(error_msg)
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
            root.destroy()
        except:
            pass
        
        return False
    
    return True


def main():
    """Main function to launch the Clean Modern GUI application"""
    try:
        # Check dependencies first
        if not check_dependencies():
            return 1
        
        # Import the correct class name
        from interface import CleanModernGUI
        
        print("🍎 Starting iPhone Automation Pro...")
        print("🎨 Launching clean modern interface...")
        print("💾 Initializing encrypted database...")
        
        # Create and run the GUI application
        app = CleanModernGUI()
        app.run()
        
        return 0
        
    except ImportError as e:
        # Handle the specific case where interface.py has the old class name
        if "CleanModernGUI" in str(e):
            try:
                # Try importing the old class name as fallback
                from interface import ModernGUI
                print("🍎 Starting iPhone Automation (fallback mode)...")
                app = ModernGUI()
                app.run()
                return 0
            except ImportError:
                pass
        
        error_msg = f"Import error: {str(e)}\n\nPlease ensure all dependencies are installed and interface.py has the correct class."
        print(error_msg)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Import Error", error_msg)
            root.destroy()
        except:
            pass
        return 1
        
    except Exception as e:
        error_msg = f"Failed to start application: {str(e)}"
        print(error_msg)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", error_msg)
            root.destroy()
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())