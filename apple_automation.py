"""
Apple iPhone automation script - Main functionality
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import Config


class AppleAutomation:
    def __init__(self, user_data=None):
        self.config = Config()
        self.user_data = user_data or self.config.DEFAULT_VALUES
        self.driver = None
        
    def setup_driver(self):
        """Initialize the Chrome driver with options"""
        options = webdriver.ChromeOptions()
        for option in self.config.BROWSER_OPTIONS:
            options.add_argument(option)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def wait_and_click(self, selectors, element_name, timeout=None):
        """Wait for element and click it using multiple selector strategies"""
        if timeout is None:
            timeout = self.config.ELEMENT_TIMEOUT
            
        if isinstance(selectors, str):
            selectors = [selectors]
            
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(self.config.SHORT_WAIT)
                element.click()
                print(f"{element_name} clicked successfully using selector: {selector}")
                return True
            except:
                continue
        
        # Fallback: try finding by text
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    btn_text = btn.text.strip().lower()
                    if any(keyword in btn_text for keyword in element_name.lower().split()):
                        btn.click()
                        print(f"{element_name} clicked successfully (text search method)")
                        return True
        except Exception as e:
            print(f"Text search method failed: {e}")
        
        print(f"Could not find {element_name}")
        return False
    
    def fill_input_field(self, selectors, value, field_name):
        """Fill input field using multiple selector strategies"""
        if isinstance(selectors, str):
            selectors = [selectors]
            
        for selector in selectors:
            try:
                field = WebDriverWait(self.driver, self.config.ELEMENT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].focus();", field)
                field.clear()
                field.send_keys(value)
                print(f"{field_name} entered: {value}")
                return True
            except:
                continue
        
        print(f"Could not find {field_name} field")
        return False
    
    def analyze_store_availability(self):
        """Analyze store availability and select first available store"""
        try:
            store_elements = WebDriverWait(self.driver, self.config.ELEMENT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.config.SELECTORS['store_elements']))
            )
            
            print(f"STORE AVAILABILITY ANALYSIS")
            print(f"Found {len(store_elements)} stores in the area:")
            print("-" * 50)
            
            available_stores = []
            unavailable_stores = []
            
            for i, store in enumerate(store_elements, 1):
                try:
                    store_name_elem = store.find_element(By.CSS_SELECTOR, self.config.SELECTORS['store_name'])
                    store_name = store_name_elem.text.strip()
                    
                    try:
                        location_elem = store.find_element(By.CSS_SELECTOR, self.config.SELECTORS['store_location'])
                        location = location_elem.text.strip()
                    except:
                        location = "Location not found"
                    
                    # Check availability
                    store_text = store.text
                    if "Available Today" in store_text:
                        available_stores.append({
                            'name': store_name,
                            'location': location,
                            'availability': "Available Today",
                            'element': store
                        })
                        print(f"AVAILABLE: {store_name}")
                        print(f"  Location: {location}")
                        print(f"  Status: Available Today")
                        print()
                    else:
                        availability = "Currently unavailable" if "unavailable" in store_text else "Status unknown"
                        unavailable_stores.append({
                            'name': store_name,
                            'location': location,
                            'availability': availability
                        })
                
                except Exception as e:
                    print(f"Error processing store {i}: {e}")
                    continue
            
            print("=" * 50)
            print("AVAILABILITY ANALYTICS:")
            print(f"Total stores found: {len(store_elements)}")
            print(f"Available today: {len(available_stores)}")
            print(f"Currently unavailable: {len(unavailable_stores)}")
            
            if available_stores:
                availability_rate = (len(available_stores) / len(store_elements)) * 100
                print(f"Availability rate: {availability_rate:.1f}%")
                
                print(f"AVAILABLE LOCATIONS ({len(available_stores)} stores):")
                for store in available_stores:
                    print(f"  - {store['name']} - {store['location']}")
                
                # Select first available store
                print(f"Selecting first available store: {available_stores[0]['name']}")
                first_store = available_stores[0]['element']
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_store)
                time.sleep(self.config.SHORT_WAIT)
                
                try:
                    store_radio = first_store.find_element(By.CSS_SELECTOR, self.config.SELECTORS['store_radio'])
                    store_radio.click()
                except:
                    first_store.click()
                
                print(f"Selected store: {available_stores[0]['name']}")
                return True
            else:
                print("No stores have the iPhone 16 Pro available for pickup today")
                return False
                
        except Exception as e:
            print(f"Error analyzing store availability: {e}")
            return False
    
    def select_pickup_time(self):
        """Select first available pickup time slot"""
        for selector in self.config.SELECTORS['pickup_time_dropdown']:
            try:
                dropdown = WebDriverWait(self.driver, self.config.ELEMENT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                print(f"Found pickup time dropdown using selector: {selector}")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
                time.sleep(self.config.SHORT_WAIT)
                
                select_obj = Select(dropdown)
                options = select_obj.options
                
                print(f"Found {len(options)} time slot options:")
                for i, option in enumerate(options):
                    option_text = option.text.strip()
                    option_value = option.get_attribute('value')
                    if option_text:
                        print(f"  Option {i}: '{option_text}' (value: {option_value})")
                
                # Select first available option
                for option in options:
                    option_text = option.text.strip()
                    option_value = option.get_attribute('value')
                    
                    if (option_text and 
                        option_value and 
                        option_value != "disabled" and
                        "Select" not in option_text and
                        "Available Windows" not in option_text and
                        not option.get_attribute('disabled')):
                        
                        try:
                            select_obj.select_by_value(option_value)
                            print(f"Selected time slot: '{option_text}' with value: {option_value}")
                            return True
                        except Exception as e:
                            continue
                
                # Fallback: select by index
                if len(options) > 1:
                    select_obj.select_by_index(1)
                    print(f"Selected time slot by index: '{options[1].text.strip()}'")
                    return True
                    
            except:
                continue
        
        print("Could not find pickup time slot dropdown")
        return False
    
    def fill_contact_form(self):
        """Fill out the contact information form"""
        print("Filling out contact form...")
        
        # Fill contact fields
        fields = [
            (self.config.SELECTORS['first_name'], self.user_data['first_name'], "First name"),
            (self.config.SELECTORS['last_name'], self.user_data['last_name'], "Last name"),
            (self.config.SELECTORS['email'], self.user_data['email'], "Email"),
            (self.config.SELECTORS['phone'], self.user_data['phone'], "Phone")
        ]
        
        for selectors, value, field_name in fields:
            self.fill_input_field(selectors, value, field_name)
            time.sleep(0.5)
        
        # Submit form by pressing Enter on phone field
        try:
            for selector in self.config.SELECTORS['phone']:
                try:
                    phone_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    phone_input.send_keys(Keys.RETURN)
                    print("Pressed Enter to submit form")
                    break
                except:
                    continue
        except:
            pass
    
    def fill_billing_info(self):
        """Fill billing information"""
        print("Filling billing information...")
        
        # Click notification checkbox
        self.wait_and_click(self.config.SELECTORS['notification_checkbox'], "notification checkbox")
        
        # Fill billing fields
        billing_fields = [
            (self.config.SELECTORS['billing_email'], self.user_data['email'], "Billing email"),
            (self.config.SELECTORS['billing_phone'], self.user_data['phone'], "Billing phone")
        ]
        
        for selectors, value, field_name in billing_fields:
            self.fill_input_field(selectors, value, field_name)
            time.sleep(0.5)
    
    def fill_payment_info(self):
        """Fill payment information"""
        print("Filling payment information...")
        
        # Select credit payment option
        try:
            credit_radio = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.config.SELECTORS['credit_payment']))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", credit_radio)
            time.sleep(self.config.SHORT_WAIT)
            self.driver.execute_script("arguments[0].click();", credit_radio)
            print("CREDIT payment option selected successfully")
            time.sleep(self.config.MEDIUM_WAIT)
        except Exception as e:
            print(f"Error selecting credit payment: {e}")
            return False
        
        # Fill credit card fields
        try:
            card_fields = [
                (self.config.SELECTORS['card_number'], self.user_data['credit_card'], "Credit card number"),
                (self.config.SELECTORS['expiry'], self.user_data['expiry_date'], "Expiry date"),
                (self.config.SELECTORS['cvc'], self.user_data['cvc'], "CVC")
            ]
            
            for selector, value, field_name in card_fields:
                if self.fill_input_field(selector, value, field_name):
                    time.sleep(self.config.SHORT_WAIT)
            
        except Exception as e:
            print(f"Error filling credit card fields: {e}")
        
        # Fill billing address
        billing_address_fields = [
            (self.config.SELECTORS['billing_first_name'], self.user_data['first_name'], "Billing first name"),
            (self.config.SELECTORS['billing_last_name'], self.user_data['last_name'], "Billing last name"),
            (self.config.SELECTORS['billing_street'], self.user_data['street_address'], "Billing street address"),
            (self.config.SELECTORS['billing_postal_code'], self.user_data['postal_code'], "Billing postal code")
        ]
        
        for selector, value, field_name in billing_address_fields:
            if self.fill_input_field(selector, value, field_name):
                time.sleep(0.5)
        
        return True
    
    def run_automation(self):
        """Main automation workflow"""
        try:
            print("Starting Apple website automation...")
            
            # Setup driver
            self.setup_driver()
            
            # Navigate to product page
            print("Opening Apple website...")
            self.driver.get(self.config.PRODUCT_URL)
            WebDriverWait(self.driver, self.config.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Page loaded successfully")
            
            # Scroll to load content
            print("Scrolling down to load content...")
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {self.config.SCROLL_PERCENTAGE});")
            time.sleep(self.config.MEDIUM_WAIT)
            
            # Click AppleCare option
            print("Clicking AppleCare option...")
            if not self.wait_and_click(self.config.SELECTORS['applecare_no'], "AppleCare option"):
                return False
            
            # Click pickup button
            print("Looking for pickup button...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['pickup_button'], "Pickup button"):
                return False
            
            # Enter zip code
            print("Looking for zip code input field...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.fill_input_field(self.config.SELECTORS['zip_input'], self.user_data['zip_code'], "Zip code"):
                return False
            
            # Submit zip code
            zip_input = self.driver.find_element(By.CSS_SELECTOR, self.config.SELECTORS['zip_input'])
            zip_input.send_keys(Keys.RETURN)
            print("Pressing Enter")
            
            # Wait for store results and analyze availability
            print("Waiting for store results to load...")
            time.sleep(self.config.LONG_WAIT)
            
            if not self.analyze_store_availability():
                return False
            
            # Continue with pickup
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['continue_pickup'], "Continue button"):
                return False
            
            # Add to bag
            print("Waiting for next page to load...")
            time.sleep(self.config.LONG_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['add_to_bag'], "Add to Bag button"):
                return False
            
            # Review bag
            print("Waiting for bag page to load...")
            time.sleep(self.config.LONG_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['review_bag'], "Review Bag button"):
                return False
            
            # Checkout
            print("Waiting for checkout page to load...")
            time.sleep(self.config.LONG_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['checkout'], "Checkout button"):
                return False
            
            # Continue as guest
            print("Waiting for checkout page to load...")
            time.sleep(self.config.LONG_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['guest_checkout'], "Continue as Guest button"):
                return False
            
            # Select pickup time
            print("Waiting for pickup time selection page...")
            time.sleep(self.config.LONG_WAIT)
            if not self.select_pickup_time():
                return False
            
            # Continue to pickup person selection
            print("Waiting for page to update...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['final_continue'], "Final Continue button"):
                return False
            
            # Select third party pickup
            print("Waiting for pickup person selection page...")
            time.sleep(self.config.LONG_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['third_party_pickup'], "Someone else to pick up option"):
                return False
            
            # Fill contact form
            print("Waiting for contact form to load...")
            time.sleep(self.config.MEDIUM_WAIT)
            self.fill_contact_form()
            
            # Fill billing info
            print("Looking for notification checkbox and billing fields...")
            time.sleep(self.config.MEDIUM_WAIT)
            self.fill_billing_info()
            
            # Continue to payment
            print("Looking for Continue to Payment button...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click(self.config.SELECTORS['continue_payment'], "Continue to Payment button"):
                return False
            
            # Fill payment information
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.fill_payment_info():
                return False
            
            # Continue to review
            print("Looking for Continue to Review button...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click("button[id='rs-checkout-continue-button-bottom']", "Continue to Review button"):
                return False
            
            # Final continue on review page
            print("Looking for final Continue button...")
            time.sleep(self.config.MEDIUM_WAIT)
            if not self.wait_and_click("button[id='rs-checkout-continue-button-bottom']", "Continue button on review page"):
                return False
            
            print("SUCCESS: All steps completed successfully!")
            print("Keeping browser open to see final results...")
            time.sleep(self.config.FINAL_WAIT)
            
            return True
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed.")


if __name__ == "__main__":
    # For testing with default values
    automation = AppleAutomation()
    automation.run_automation()