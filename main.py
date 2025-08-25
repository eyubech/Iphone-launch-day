import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def parse_iphone_data(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return []

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def safe_click(driver, element, method_name):
    """Try multiple click methods"""
    try:
        # Scroll to element first
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        
        # Try regular click first
        element.click()
        print(f"{method_name}: Regular click successful")
        return True
    except Exception as e1:
        try:
            # Try JavaScript click
            driver.execute_script("arguments[0].click();", element)
            print(f"{method_name}: JavaScript click successful")
            return True
        except Exception as e2:
            print(f"{method_name}: Both click methods failed - {e1}, {e2}")
            return False

def select_iphone_model(driver, version):
    print(f"Selecting iPhone model for: {version}")
    try:
        # Wait for page to load
        time.sleep(3)
        
        # Simple approach - look for any model selection inputs
        model_inputs = driver.find_elements(By.XPATH, '//input[@name="dimensionScreensize"]')
        
        if len(model_inputs) >= 2:
            if "pro max" in version.lower():
                print("Trying to select Pro Max (index 1)")
                return safe_click(driver, model_inputs[1], "Model Selection")
            else:
                print("Trying to select Pro (index 0)")
                return safe_click(driver, model_inputs[0], "Model Selection")
        else:
            print(f"Found {len(model_inputs)} model inputs, expected at least 2")
            return False
            
    except Exception as e:
        print(f"Error selecting model: {e}")
        return False

def select_color_option(driver, color_index):
    print(f"Selecting color option: {color_index}")
    try:
        time.sleep(2)
        
        # Look for color inputs
        color_inputs = driver.find_elements(By.XPATH, '//input[contains(@class, "colornav-value")]')
        
        if len(color_inputs) >= color_index:
            selected_input = color_inputs[color_index - 1]  # Convert to 0-based index
            return safe_click(driver, selected_input, "Color Selection")
        else:
            print(f"Found {len(color_inputs)} colors, requested index {color_index}")
            return False
            
    except Exception as e:
        print(f"Error selecting color: {e}")
        return False

def select_storage_option(driver, storage_index):
    print(f"Selecting storage option: {storage_index}")
    try:
        time.sleep(2)
        
        # Look for storage inputs
        storage_inputs = driver.find_elements(By.XPATH, '//input[@name="dimensionCapacity"]')
        
        if len(storage_inputs) >= storage_index:
            selected_input = storage_inputs[storage_index - 1]  # Convert to 0-based index
            return safe_click(driver, selected_input, "Storage Selection")
        else:
            print(f"Found {len(storage_inputs)} storage options, requested index {storage_index}")
            return False
            
    except Exception as e:
        print(f"Error selecting storage: {e}")
        return False

def select_no_trade_in(driver):
    print("Selecting no trade in")
    try:
        time.sleep(2)
        
        # Look for trade-in options
        trade_selectors = [
            '//input[@id="noTradeIn"]',
            '//input[@value="notradein"]'
        ]
        
        for selector in trade_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if safe_click(driver, element, "Trade-in Selection"):
                    return True
            except NoSuchElementException:
                continue
        
        print("No trade-in option not found")
        return False
        
    except Exception as e:
        print(f"Error selecting no trade in: {e}")
        return False

def select_purchase_option(driver):
    print("Selecting purchase option")
    try:
        time.sleep(3)
        
        # Look for purchase options
        purchase_selectors = [
            '//input[@value="fullprice"]',
            '//input[@name="purchase_option_group"]'
        ]
        
        for selector in purchase_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    if safe_click(driver, elements[0], "Purchase Option"):
                        return True
            except NoSuchElementException:
                continue
        
        print("Purchase option not found")
        return False
        
    except Exception as e:
        print(f"Error selecting purchase option: {e}")
        return False

def select_carrier(driver):
    print("Selecting carrier")
    try:
        time.sleep(3)
        
        # Look for carrier options - updated based on your HTML
        carrier_selectors = [
            '//input[@value="UNLOCKED/US"]',
            '//input[@name="carrierModel"][@value="UNLOCKED/US"]',
            '//input[@id=":rn:"]',
            '//input[@value="unlocked"]',
            '//input[@name="carrierModel"]'
        ]
        
        for selector in carrier_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found carrier element with selector: {selector}")
                    if safe_click(driver, elements[0], "Carrier Selection"):
                        return True
            except NoSuchElementException:
                continue
        
        # If specific selectors don't work, try finding any carrier input
        try:
            all_carrier_inputs = driver.find_elements(By.XPATH, '//input[@name="carrierModel"]')
            print(f"Found {len(all_carrier_inputs)} carrier options")
            
            for i, carrier_input in enumerate(all_carrier_inputs):
                try:
                    value = carrier_input.get_attribute("value")
                    print(f"Carrier option {i+1}: {value}")
                    
                    # Look for unlocked option
                    if "UNLOCKED" in value.upper():
                        print(f"Selecting unlocked option: {value}")
                        if safe_click(driver, carrier_input, "Carrier Selection"):
                            return True
                except Exception as e:
                    print(f"Error checking carrier option {i+1}: {e}")
                    continue
            
            # If no unlocked found, try first option
            if all_carrier_inputs:
                print("No unlocked option found, trying first carrier option")
                if safe_click(driver, all_carrier_inputs[0], "Carrier Selection"):
                    return True
                    
        except Exception as e:
            print(f"Error finding carrier inputs: {e}")
        
        print("Carrier option not found")
        return False
        
    except Exception as e:
        print(f"Error selecting carrier: {e}")
        return False

def select_no_warranty(driver):
    print("Selecting no warranty (AppleCare)")
    try:
        time.sleep(3)
        
        # Look for AppleCare/warranty options - based on your HTML
        warranty_selectors = [
            '//input[@name="applecare" and @value="noapplecare"]',
            '//input[@data-autom="noapplecare"]',
            '//input[@id=":r1j:"]',
            '//input[@name="applecare"][@value="noapplecare"]'
        ]
        
        for selector in warranty_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"Found warranty element with selector: {selector}")
                    if safe_click(driver, elements[0], "No Warranty Selection"):
                        return True
            except NoSuchElementException:
                continue
        
        # If specific selectors don't work, try finding any AppleCare input
        try:
            all_warranty_inputs = driver.find_elements(By.XPATH, '//input[@name="applecare"]')
            print(f"Found {len(all_warranty_inputs)} warranty options")
            
            for i, warranty_input in enumerate(all_warranty_inputs):
                try:
                    value = warranty_input.get_attribute("value")
                    data_autom = warranty_input.get_attribute("data-autom")
                    print(f"Warranty option {i+1}: value='{value}', data-autom='{data_autom}'")
                    
                    # Look for no warranty option
                    if value and ("no" in value.lower() or "noapplecare" in value.lower()):
                        print(f"Selecting no warranty option: {value}")
                        if safe_click(driver, warranty_input, "No Warranty Selection"):
                            return True
                    elif data_autom and "noapplecare" in data_autom.lower():
                        print(f"Selecting no warranty option by data-autom: {data_autom}")
                        if safe_click(driver, warranty_input, "No Warranty Selection"):
                            return True
                except Exception as e:
                    print(f"Error checking warranty option {i+1}: {e}")
                    continue
            
            # If no "no warranty" found, try first option (often the no warranty option)
            if all_warranty_inputs:
                print("No clear 'no warranty' option found, trying first warranty option")
                if safe_click(driver, all_warranty_inputs[0], "Warranty Selection"):
                    return True
                    
        except Exception as e:
            print(f"Error finding warranty inputs: {e}")
        
        print("Warranty option not found")
        return False
        
    except Exception as e:
        print(f"Error selecting warranty: {e}")
        return False

def click_buy_button(driver):
    print("Looking for buy/add to bag button...")
    try:
        time.sleep(3)
        
        # Simple approach - look for any button with buy/add text
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        print(f"Found {len(all_buttons)} buttons on page")
        
        for i, button in enumerate(all_buttons):
            try:
                button_text = button.text.strip().lower()
                print(f"Button {i+1}: '{button_text}'")
                
                if any(keyword in button_text for keyword in ["add to bag", "buy", "add", "cart"]):
                    print(f"Trying to click button: '{button_text}'")
                    if button.is_enabled() and button.is_displayed():
                        if safe_click(driver, button, "Buy Button"):
                            time.sleep(5)
                            return True
                    else:
                        print(f"Button not clickable - enabled: {button.is_enabled()}, visible: {button.is_displayed()}")
                        
            except Exception as e:
                print(f"Error checking button {i+1}: {e}")
                continue
        
        print("No suitable buy button found")
        return False
        
    except Exception as e:
        print(f"Error in click_buy_button: {e}")
        return False

def process_single_iphone(driver, item, tab_index=0):
    try:
        iphone_version = item.get('version', 'Unknown')
        pieces = item.get('pieces', 1)
        storage = item.get('storage', 1)
        color = item.get('color', 1)
        
        print(f"\n{'='*60}")
        print(f"Processing iPhone {iphone_version}")
        print(f"Storage Index: {storage}, Color Index: {color}, Pieces: {pieces}")
        print(f"{'='*60}")
        
        url = "https://www.apple.com/shop/buy-iphone/iphone-16-pro"
        print(f"Opening: {url}")
        
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        # Process each step
        steps = [
            ("Model Selection", lambda: select_iphone_model(driver, iphone_version)),
            ("Color Selection", lambda: select_color_option(driver, color)),
            ("Storage Selection", lambda: select_storage_option(driver, storage)),
            ("No Trade-in", lambda: select_no_trade_in(driver)),
            ("Purchase Option", lambda: select_purchase_option(driver)),
            ("Carrier Selection", lambda: select_carrier(driver)),
            ("No Warranty", lambda: select_no_warranty(driver)),
            ("Buy Button", lambda: click_buy_button(driver))
        ]
        
        for step_name, step_function in steps:
            print(f"\n--- {step_name} ---")
            try:
                success = step_function()
                if success:
                    print(f"✓ {step_name} completed successfully")
                else:
                    print(f"✗ {step_name} failed")
                    # Don't stop - continue to next step
            except Exception as e:
                print(f"✗ {step_name} error: {e}")
        
        print(f"\nConfiguration process completed for {iphone_version}")
        return True
        
    except Exception as e:
        print(f"Error processing iPhone: {e}")
        return False

def process_iphone_data_multitab(json_file_path, wait_time=15):
    iphone_data = parse_iphone_data(json_file_path)
    
    if not iphone_data:
        print("No iPhone data found or error reading file")
        return
    
    driver = setup_driver()
    if not driver:
        return
    
    try:
        print(f"Starting to process {len(iphone_data)} iPhone configurations...")
        
        for i, item in enumerate(iphone_data):
            print(f"\n\nProcessing item {i+1} of {len(iphone_data)}")
            process_single_iphone(driver, item)
            
            if i < len(iphone_data) - 1:  # If not the last item
                print(f"\nWaiting {wait_time} seconds before next configuration...")
                time.sleep(wait_time)
                
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nClosing browser...")
        try:
            driver.quit()
            print("Browser closed successfully")
        except:
            print("Error closing browser")

if __name__ == "__main__":
    json_file_path = "data.json"
    wait_time = 15
    
    print("iPhone 16 Pro/Pro Max Data Parser - Simplified Version")
    print("======================================================")
    print(f"Wait time between items: {wait_time} seconds")
    print("This version processes one item at a time for better reliability")
    
    process_iphone_data_multitab(json_file_path, wait_time)