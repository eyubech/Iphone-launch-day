import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class IPhoneAutomation:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or self._default_log
        self.driver = None
        self.should_stop = False
        
        # URL mapping for different iPhone models
        self.model_urls = {
            "14": "https://www.apple.com/shop/buy-iphone/iphone-14",
            "14 Plus": "https://www.apple.com/shop/buy-iphone/iphone-14",
            "14 Pro": "https://www.apple.com/shop/buy-iphone/iphone-14-pro",
            "14 Pro Max": "https://www.apple.com/shop/buy-iphone/iphone-14-pro",
            "15": "https://www.apple.com/shop/buy-iphone/iphone-15",
            "15 Plus": "https://www.apple.com/shop/buy-iphone/iphone-15",
            "15 Pro": "https://www.apple.com/shop/buy-iphone/iphone-15-pro",
            "15 Pro Max": "https://www.apple.com/shop/buy-iphone/iphone-15-pro",
            "16": "https://www.apple.com/shop/buy-iphone/iphone-16",
            "16 Plus": "https://www.apple.com/shop/buy-iphone/iphone-16",
            "16 Pro": "https://www.apple.com/shop/buy-iphone/iphone-16-pro",
            "16 Pro Max": "https://www.apple.com/shop/buy-iphone/iphone-16-pro"
        }
    
    def _default_log(self, message, level="INFO"):
        """Default logging function"""
        print(f"[{level}] {message}")
    
    def log(self, message, level="INFO"):
        """Log a message"""
        self.log_callback(message, level)
    
    def stop(self):
        """Signal to stop the automation"""
        self.should_stop = True
        self.log("Stop signal received", "WARNING")
    
    def setup_driver(self):
        """Setup Chrome WebDriver with optimized options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.log("Chrome driver initialized successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to setup Chrome driver: {str(e)}", "ERROR")
            return False
    
    def safe_click(self, element, element_name):
        """Try multiple click methods for better reliability"""
        if self.should_stop:
            return False
            
        try:
            # Scroll to element first
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Try regular click first
            element.click()
            self.log(f"✓ {element_name} clicked successfully", "SUCCESS")
            return True
            
        except Exception as e1:
            try:
                # Try JavaScript click as fallback
                self.driver.execute_script("arguments[0].click();", element)
                self.log(f"✓ {element_name} clicked via JavaScript", "SUCCESS")
                return True
                
            except Exception as e2:
                self.log(f"✗ Failed to click {element_name}: {str(e1)}", "ERROR")
                return False
    
    def select_model_variant(self, version):
        """Select iPhone model variant (Pro vs Pro Max)"""
        self.log(f"Selecting model variant for: {version}")
        
        try:
            time.sleep(3)
            model_inputs = self.driver.find_elements(By.XPATH, '//input[@name="dimensionScreensize"]')
            
            if len(model_inputs) >= 2:
                if "pro max" in version.lower():
                    self.log("Selecting Pro Max variant")
                    return self.safe_click(model_inputs[1], "Pro Max Model")
                else:
                    self.log("Selecting Pro variant")
                    return self.safe_click(model_inputs[0], "Pro Model")
            else:
                self.log(f"Expected at least 2 model options, found {len(model_inputs)}", "WARNING")
                if model_inputs:
                    return self.safe_click(model_inputs[0], "Default Model")
                return False
                
        except Exception as e:
            self.log(f"Error selecting model variant: {str(e)}", "ERROR")
            return False
    
    def select_color(self, color_index):
        """Select color option by index"""
        self.log(f"Selecting color option {color_index}")
        
        try:
            time.sleep(2)
            color_inputs = self.driver.find_elements(By.XPATH, '//input[contains(@class, "colornav-value")]')
            
            if len(color_inputs) >= color_index:
                selected_input = color_inputs[color_index - 1]
                return self.safe_click(selected_input, f"Color {color_index}")
            else:
                self.log(f"Color index {color_index} not available. Found {len(color_inputs)} colors", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error selecting color: {str(e)}", "ERROR")
            return False
    
    def select_storage(self, storage_index):
        """Select storage option by index"""
        self.log(f"Selecting storage option {storage_index}")
        
        try:
            time.sleep(2)
            storage_inputs = self.driver.find_elements(By.XPATH, '//input[@name="dimensionCapacity"]')
            
            if len(storage_inputs) >= storage_index:
                selected_input = storage_inputs[storage_index - 1]
                return self.safe_click(selected_input, f"Storage {storage_index}")
            else:
                self.log(f"Storage index {storage_index} not available. Found {len(storage_inputs)} options", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error selecting storage: {str(e)}", "ERROR")
            return False
    
    def select_no_trade_in(self):
        """Select no trade-in option"""
        self.log("Selecting no trade-in option")
        
        try:
            time.sleep(2)
            
            selectors = [
                '//input[@id="noTradeIn"]',
                '//input[@value="notradein"]',
                '//input[contains(@value, "no")]'
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if self.safe_click(element, "No Trade-in"):
                        return True
                except NoSuchElementException:
                    continue
            
            self.log("No trade-in option not found", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Error selecting no trade-in: {str(e)}", "ERROR")
            return False
    
    def select_purchase_option(self):
        """Select full price purchase option"""
        self.log("Selecting purchase option")
        
        try:
            time.sleep(3)
            
            selectors = [
                '//input[@value="fullprice"]',
                '//input[@name="purchase_option_group"]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements and self.safe_click(elements[0], "Full Price Purchase"):
                        return True
                except NoSuchElementException:
                    continue
            
            self.log("Purchase option not found", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Error selecting purchase option: {str(e)}", "ERROR")
            return False
    
    def select_carrier(self):
        """Select unlocked carrier option"""
        self.log("Selecting carrier (Unlocked)")
        
        try:
            time.sleep(3)
            
            # Try to find unlocked option
            carrier_inputs = self.driver.find_elements(By.XPATH, '//input[@name="carrierModel"]')
            self.log(f"Found {len(carrier_inputs)} carrier options")
            
            for i, carrier_input in enumerate(carrier_inputs):
                try:
                    value = carrier_input.get_attribute("value")
                    if value and "UNLOCKED" in value.upper():
                        self.log(f"Found unlocked option: {value}")
                        return self.safe_click(carrier_input, "Unlocked Carrier")
                except Exception:
                    continue
            
            # If no unlocked found, try first option
            if carrier_inputs:
                self.log("No unlocked option found, selecting first carrier")
                return self.safe_click(carrier_inputs[0], "Default Carrier")
            
            self.log("No carrier options found", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Error selecting carrier: {str(e)}", "ERROR")
            return False
    
    def select_no_warranty(self):
        """Select no AppleCare option"""
        self.log("Selecting no warranty/AppleCare")
        
        try:
            time.sleep(3)
            
            warranty_inputs = self.driver.find_elements(By.XPATH, '//input[@name="applecare"]')
            self.log(f"Found {len(warranty_inputs)} warranty options")
            
            for warranty_input in warranty_inputs:
                try:
                    value = warranty_input.get_attribute("value")
                    data_autom = warranty_input.get_attribute("data-autom")
                    
                    if (value and "no" in value.lower()) or (data_autom and "noapplecare" in data_autom.lower()):
                        return self.safe_click(warranty_input, "No AppleCare")
                except Exception:
                    continue
            
            # Try first option if no specific "no" option found
            if warranty_inputs:
                self.log("No clear 'no warranty' option found, trying first option")
                return self.safe_click(warranty_inputs[0], "Default Warranty")
            
            self.log("No warranty options found", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Error selecting warranty: {str(e)}", "ERROR")
            return False
    
    def click_buy_button(self):
        """Click the buy/add to bag button"""
        self.log("Looking for buy button...")
        
        try:
            time.sleep(3)
            
            # Look for buy buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            for button in buttons:
                try:
                    button_text = button.text.strip().lower()
                    
                    if any(keyword in button_text for keyword in ["add to bag", "buy", "add", "cart"]):
                        if button.is_enabled() and button.is_displayed():
                            self.log(f"Found buy button: '{button_text}'")
                            if self.safe_click(button, "Buy Button"):
                                time.sleep(5)
                                return True
                        else:
                            self.log(f"Buy button not clickable: '{button_text}'", "WARNING")
                            
                except Exception:
                    continue
            
            self.log("No suitable buy button found", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Error clicking buy button: {str(e)}", "ERROR")
            return False
    
    def process_single_configuration(self, config):
        """Process a single iPhone configuration"""
        if self.should_stop:
            return False
            
        try:
            version = config.get('version', 'Unknown')
            color = config.get('color', 1)
            storage = config.get('storage', 1)
            pieces = config.get('pieces', 1)
            
            self.log(f"Processing: {version} (Color: {color}, Storage: {storage}, Qty: {pieces})", "INFO")
            
            # Get URL for the model
            url = self.model_urls.get(version)
            if not url:
                self.log(f"No URL found for model: {version}", "ERROR")
                return False
            
            self.log(f"Opening: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)
            
            if self.should_stop:
                return False
            
            # Process configuration steps
            steps = [
                ("Model Selection", lambda: self.select_model_variant(version)),
                ("Color Selection", lambda: self.select_color(color)),
                ("Storage Selection", lambda: self.select_storage(storage)),
                ("No Trade-in", lambda: self.select_no_trade_in()),
                ("Purchase Option", lambda: self.select_purchase_option()),
                ("Carrier Selection", lambda: self.select_carrier()),
                ("No Warranty", lambda: self.select_no_warranty()),
                ("Buy Button", lambda: self.click_buy_button())
            ]
            
            success_count = 0
            for step_name, step_function in steps:
                if self.should_stop:
                    return False
                    
                self.log(f"Executing: {step_name}")
                try:
                    if step_function():
                        success_count += 1
                    else:
                        self.log(f"Step failed: {step_name}", "WARNING")
                except Exception as e:
                    self.log(f"Step error: {step_name} - {str(e)}", "ERROR")
                
                # Small delay between steps
                time.sleep(1)
            
            success_rate = (success_count / len(steps)) * 100
            self.log(f"Configuration completed: {success_count}/{len(steps)} steps successful ({success_rate:.1f}%)", 
                    "SUCCESS" if success_rate >= 70 else "WARNING")
            
            return success_rate >= 50  # Consider successful if at least 50% of steps completed
            
        except Exception as e:
            self.log(f"Error processing configuration: {str(e)}", "ERROR")
            return False
    
    def process_configurations(self, configurations):
        """Process multiple iPhone configurations"""
        if not self.setup_driver():
            return False
        
        try:
            total_configs = len(configurations)
            successful_configs = 0
            
            self.log(f"Starting automation for {total_configs} configuration(s)", "INFO")
            
            for i, config in enumerate(configurations, 1):
                if self.should_stop:
                    self.log("Automation stopped by user", "WARNING")
                    break
                
                self.log(f"Processing configuration {i}/{total_configs}", "INFO")
                
                if self.process_single_configuration(config):
                    successful_configs += 1
                
                # Wait between configurations (except for the last one)
                if i < total_configs and not self.should_stop:
                    self.log("Waiting 15 seconds before next configuration...")
                    for second in range(15):
                        if self.should_stop:
                            break
                        time.sleep(1)
            
            # Final summary
            success_rate = (successful_configs / total_configs) * 100
            self.log(f"Automation completed: {successful_configs}/{total_configs} configurations successful ({success_rate:.1f}%)", 
                    "SUCCESS" if success_rate >= 70 else "WARNING")
            
            return successful_configs > 0
            
        except Exception as e:
            self.log(f"Fatal error in automation: {str(e)}", "ERROR")
            return False
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.log("Browser closed successfully", "INFO")
            except Exception as e:
                self.log(f"Error closing browser: {str(e)}", "WARNING")
            finally:
                self.driver = None
    
    def get_available_options(self, option_type):
        """Get available options from the current page"""
        try:
            if option_type == "colors":
                elements = self.driver.find_elements(By.XPATH, '//input[contains(@class, "colornav-value")]')
            elif option_type == "storage":
                elements = self.driver.find_elements(By.XPATH, '//input[@name="dimensionCapacity"]')
            elif option_type == "models":
                elements = self.driver.find_elements(By.XPATH, '//input[@name="dimensionScreensize"]')
            else:
                return []
            
            options = []
            for i, element in enumerate(elements, 1):
                try:
                    # Try to get descriptive text
                    parent = element.find_element(By.XPATH, '..')
                    text = parent.text.strip()
                    if text:
                        options.append(f"{i}: {text}")
                    else:
                        options.append(f"Option {i}")
                except:
                    options.append(f"Option {i}")
            
            return options
            
        except Exception as e:
            self.log(f"Error getting {option_type} options: {str(e)}", "ERROR")
            return []
    
    def take_screenshot(self, filename_prefix="screenshot"):
        """Take a screenshot for debugging purposes"""
        try:
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{timestamp}.png"
                self.driver.save_screenshot(filename)
                self.log(f"Screenshot saved: {filename}", "INFO")
                return filename
        except Exception as e:
            self.log(f"Error taking screenshot: {str(e)}", "ERROR")
            return None
    
    def wait_for_element(self, locator, timeout=10):
        """Wait for an element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, locator, timeout=10):
        """Wait for an element to be clickable"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            return None
    
    def scroll_to_element(self, element):
        """Scroll to an element smoothly"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            return True
        except Exception as e:
            self.log(f"Error scrolling to element: {str(e)}", "ERROR")
            return False
    
    def check_page_errors(self):
        """Check for common page errors"""
        try:
            # Check for error messages
            error_selectors = [
                '//div[contains(@class, "error")]',
                '//div[contains(@class, "alert")]',
                '//div[contains(text(), "error")]',
                '//div[contains(text(), "Error")]',
                '//div[contains(text(), "unavailable")]'
            ]
            
            for selector in error_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    for element in elements:
                        if element.is_displayed():
                            error_text = element.text.strip()
                            if error_text:
                                self.log(f"Page error detected: {error_text}", "ERROR")
                                return True
            
            return False
            
        except Exception:
            return False
    
    def handle_popups(self):
        """Handle common popups and overlays"""
        try:
            # Common popup selectors
            popup_selectors = [
                '//button[contains(text(), "Close")]',
                '//button[contains(text(), "×")]',
                '//button[@aria-label="Close"]',
                '//div[contains(@class, "modal")]//button',
                '//div[contains(@class, "overlay")]//button'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.safe_click(element, "Popup Close")
                            self.log("Closed popup/overlay", "INFO")
                            time.sleep(1)
                            return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def verify_page_loaded(self, expected_elements=None):
        """Verify that the page has loaded correctly"""
        try:
            # Wait for basic page structure
            body = self.wait_for_element((By.TAG_NAME, "body"), timeout=15)
            if not body:
                self.log("Page body not found", "ERROR")
                return False
            
            # Check for loading indicators
            loading_selectors = [
                '//div[contains(@class, "loading")]',
                '//div[contains(@class, "spinner")]',
                '//div[contains(text(), "Loading")]'
            ]
            
            # Wait for loading to complete
            for _ in range(10):
                loading_found = False
                for selector in loading_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if any(elem.is_displayed() for elem in elements):
                        loading_found = True
                        break
                
                if not loading_found:
                    break
                
                time.sleep(1)
            
            # Check for expected elements if provided
            if expected_elements:
                for locator in expected_elements:
                    if not self.wait_for_element(locator, timeout=5):
                        self.log(f"Expected element not found: {locator}", "WARNING")
                        return False
            
            self.log("Page loaded successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error verifying page load: {str(e)}", "ERROR")
            return False