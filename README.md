# Apple iPhone Automation Pro

A GUI-based automation tool for Apple iPhone purchasing with encrypted data storage and intelligent store analysis.

## Prerequisites

- Python 3.7 or higher
- Chrome browser
- Internet connection

## Installation

### Windows

1. **Install Python**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Download the project files**
   - Extract all files to a folder (e.g., `C:\iphone-automation`)

3. **Open Command Prompt**
   - Press `Win + R`, type `cmd`, press Enter
   - Navigate to project folder:
     ```cmd
     cd C:\iphone-automation
     ```

4. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```cmd
   python main.py
   ```

### macOS

1. **Install Python** (if not already installed)
   ```bash
   # Using Homebrew (recommended)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install python
   
   # Or download from python.org
   ```

2. **Download and extract project files**
   ```bash
   # Navigate to your downloads folder or wherever you extracted the files
   cd ~/Downloads/iphone-automation
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python3 main.py
   ```

### Linux (Ubuntu/Debian)

1. **Install Python and pip**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-tk
   ```

2. **Download and extract project files**
   ```bash
   cd ~/Downloads/iphone-automation
   # or wherever you extracted the files
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python3 main.py
   ```

### Linux (CentOS/RHEL/Fedora)

1. **Install Python and pip**
   ```bash
   # For CentOS/RHEL
   sudo yum install python3 python3-pip python3-tkinter
   
   # For Fedora
   sudo dnf install python3 python3-pip python3-tkinter
   ```

2. **Download and extract project files**
   ```bash
   cd ~/Downloads/iphone-automation
   ```

3. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python3 main.py
   ```

## Troubleshooting

### Chrome Driver Issues
If you encounter ChromeDriver errors:
- Ensure Chrome browser is installed and updated
- Selenium 4.15+ automatically manages ChromeDriver

### Permission Errors (Linux/macOS)
If you get permission errors during pip install:
```bash
pip3 install --user -r requirements.txt
```

### tkinter Not Found (Linux)
If you get "tkinter not found" error:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter

# Fedora
sudo dnf install python3-tkinter
```

### Python Command Not Found
- **Windows**: Reinstall Python with "Add to PATH" checked
- **macOS**: Use `python3` instead of `python`
- **Linux**: Install python3 package

## Quick Start

1. Run `python main.py` (or `python3 main.py` on macOS/Linux)
2. Add payment card in "Payment Cards" tab
3. Add pickup person in "Pickup Persons" tab
4. Add location in "Settings" tab
5. Go to "Automation" tab and click "Start Automation"

## File Structure

```
project-folder/
├── main.py              # Application entry point
├── interface.py         # GUI interface
├── apple_automation.py  # Automation logic
├── database.py          # Data storage
├── config.py           # Configuration
├── requirements.txt    # Dependencies
└── README.md           # This file
```

## Security

- All payment information is encrypted
- Data stored locally only
- No data transmitted to external servers

## Note

This tool is for educational purposes. Ensure compliance with Apple's terms of service.