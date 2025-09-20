# Installation Guide

## Prerequisites

- Python 3.7 or higher
- Windows 10/11
- Chrome browser installed

## Installation Steps

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Verify installation by opening Command Prompt and typing:
   ```cmd
   python --version
   ```


### Step 2: Download and Extract Project

1. Extract the project files to your **Desktop** folder
2. Open Command Prompt as Administrator
3. Navigate to the project folder on Desktop:
   ```cmd
   cd Desktop\AppleAutomation
   ```

### Step 3: Install Required Libraries

Run these pip commands:

```cmd
pip install selenium
pip install cryptography
pip install psutil
pip install webdriver-manager
pip install selenium-wire
```

### Step 4: Run the Application

```cmd
python main.py
```