import time
import sys
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from config import Config
from bright_data_proxy import BrightDataProxy
from email_manager import EmailManager


class AppleAutomation:
    def __init__(self, card_data=None, person_data=None, settings_data=None, user_data=None, 
                 product_url=None, use_proxy=False, process_num=1):
        self.config = Config()
        self.driver = None
        self._stopped = False
        self.purchase_count = 0
        self.max_purchases = 2
        self.saved_link = ''
        self.error_count = 0
        self.max_errors = 3
        
        self.proxy = BrightDataProxy()
        self.use_proxy = use_proxy
        self.process_num = process_num
        self.email_manager = EmailManager()
        self.process_email = None
        
        if use_proxy:
            self.proxy.enable_proxy()
            print(f"Process {process_num}: Proxy enabled with session {self.proxy.generate_session_id(process_num)}")
        else:
            self.proxy.disable_proxy()
            print(f"Process {process_num}: Running without proxy")
        
        if product_url:
            self.config.PRODUCT_URL = product_url
            print(f"Using custom product URL: {product_url}")
        
        if card_data and person_data and settings_data:
            self.user_data = self._combine_automation_data(card_data, person_data, settings_data)
        elif user_data:
            self.user_data = user_data
        else:
            self.user_data = self.config.DEFAULT_VALUES

    def get_process_email(self):
        if not self.process_email:
            try:
                self.process_email = self.email_manager.get_next_email(self.process_num)
                print(f"Process {self.process_num}: Assigned email: {self.process_email}")
            except Exception as e:
                print(f"Process {self.process_num}: Error getting email: {e}")
                self.process_email = self.user_data.get('email', 'default@example.com')
        
        return self.process_email

    def mark_email_status(self, success=True):
        if self.process_email:
            try:
                if success:
                    self.email_manager.mark_email_completed(self.process_email)
                    print(f"Process {self.process_num}: Email {self.process_email} marked as completed")
                else:
                    self.email_manager.mark_email_failed(self.process_email)
                    print(f"Process {self.process_num}: Email {self.process_email} marked as failed")
            except Exception as e:
                print(f"Process {self.process_num}: Error updating email status: {e}")

    def _combine_automation_data(self, card_data, person_data, settings_data):
        user_info = card_data.get('user_info', {})
        process_email = self.get_process_email()
        
        return {
            'zip_code': settings_data['zip_code'],
            'first_name': user_info.get('first_name', person_data['first_name']),
            'last_name': user_info.get('last_name', person_data['last_name']),
            'email': process_email,
            'phone': user_info.get('phone', person_data['phone'])
        }

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-automation")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        for option in self.config.BROWSER_OPTIONS:
            options.add_argument(option)
            
        if self.use_proxy:
            proxy_options = self.proxy.get_chrome_proxy_options(self.process_num)
            for proxy_option in proxy_options:
                options.add_argument(proxy_option)
            print(f"Process {self.process_num}: Chrome configured with proxy")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"Process {self.process_num}: Failed to setup driver - {str(e)}")
            return False
        
    def stop(self):
        self._stopped = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    # STEP 1: Click No Coverage
    def click_applecare_no_coverage(self):
        if self._stopped:
            return False
        
        print("STEP 1: Looking for AppleCare no coverage option...")
        
        try:
            # Method 1: By name attribute (most common)
            radios = self.driver.find_elements(By.NAME, "applecare-options")
            if len(radios) >= 3:
                print(f"Found {len(radios)} AppleCare options, clicking third option (no coverage)")
                radios[2].click()
                print("✓ No coverage selected successfully")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: By CSS selectors
        selectors = [
            "[class*='applecare'][class*='no']",
            "[data-autom*='noapple']",
            "input[type='radio'][value*='no']",
            ".rf-product-options input[type='radio']:last-child"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.click()
                print("✓ No coverage selected successfully")
                time.sleep(2)
                return True
            except:
                continue
        
        print("✗ Could not find AppleCare no coverage option")
        return False

    # STEP 2: Add to Bag
    def add_to_bag(self):
        if self._stopped:
            return False
        
        print(f"STEP 2: Adding iPhone {self.purchase_count + 1} to bag...")
        
        selectors = [
            'button[name="add-to-cart"]',
            'button[data-autom="add-to-cart"]',
            '.as-purchaseinfo-button button',
            'form button[type="submit"]',
            'button[class*="add-to-cart"]',
            '.button[data-autom="add-to-cart"]'
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                element.click()
                print(f"✓ iPhone {self.purchase_count + 1} added to bag successfully")
                time.sleep(3)
                return True
            except:
                continue
        
        print("✗ Could not find add to bag button")
        return False

    # STEP 3: Handle going back for second iPhone or proceed to checkout
    def handle_bag_page(self):
        if self._stopped:
            return False
            
        print("Waiting for bag page to load...")
        time.sleep(3)
        
        self.purchase_count += 1
        print(f"iPhone {self.purchase_count} added to bag")
        
        if self.purchase_count < self.max_purchases:
            print(f"STEP 3: Going back for iPhone {self.purchase_count + 1}...")
            print(f"Navigating back to: {self.saved_link}")
            
            try:
                self.driver.get(self.saved_link)
                print("Successfully navigated back to product page")
                
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print("Product page reloaded successfully")
                time.sleep(2)
                
                # Repeat the process for second iPhone
                return self.run_purchase_flow()
                
            except Exception as e:
                print(f"Error navigating back to product page: {e}")
                return False
        else:
            print("STEP 3: Both iPhones added, proceeding to checkout")
            return self.proceed_to_checkout()

    # STEP 4: Proceed to Checkout
    def proceed_to_checkout(self):
        if self._stopped:
            return False
        
        print("STEP 4: Looking for checkout button...")
        
        proceed_selectors = [
            'button[name="proceed"]',
            'button[data-autom="proceed"]',
            '.button.button-block[data-autom="proceed"]',
            'form button[type="submit"]',
            'button[class*="button-block"]'
        ]
        
        for selector in proceed_selectors:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                element.click()
                print("✓ Proceed to checkout clicked successfully")
                time.sleep(3)
                return self.handle_checkout_flow()
            except:
                continue
        
        print("✗ Could not find proceed to checkout button")
        return False

    # STEP 5: Handle Checkout Flow
    def handle_checkout_flow(self):
        if self._stopped:
            return False
        
        print("STEP 5: Handling checkout flow...")
        time.sleep(3)
        
        checkout_selectors = [
            'button[id="shoppingCart.actions.navCheckoutOtherPayments"]',
            'button.button.button-block.rs-bag-checkout-otheroptions',
            '.rs-bag-checkoutbutton button',
            'button[class*="checkout"]',
            '.rs-bag-checkoutbuttons-wrapper button',
            'button[type="button"][class*="button-block"]'
        ]
        
        for selector in checkout_selectors:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                element.click()
                print("✓ Checkout button clicked successfully")
                time.sleep(3)
                return self.handle_guest_login()
            except:
                continue
        
        print("✗ Could not find checkout button")
        return False

    # STEP 6: Continue as Guest
    def handle_guest_login(self):
        if self._stopped:
            return False
        
        print("STEP 6: Continue as guest...")
        
        guest_selectors = [
            'button[data-autom="guest-checkout-btn"]',
            'button[id="signin.guestLogin.guestLogin"]',
            '.form-button[data-autom="guest-checkout-btn"]',
            'button[class*="guest-checkout"]',
            '.rs-sign-in-sidebar button',
            'button[type="button"][class*="form-button"]'
        ]
        
        for selector in guest_selectors:
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)
                element.click()
                print("✓ Guest login clicked successfully")
                time.sleep(5)
                return self.handle_pickup_section()
            except:
                continue
        
        print("✗ Could not find guest login button")
        return False

    # STEP 7: Click pickup button (mandatory before zip code)
    def handle_pickup_section(self):
        if self._stopped:
            return False
        
        print("STEP 7: Looking for pickup button (segmented control)...")
        time.sleep(5)  # Wait for page to load
        
        # Look for segmented control buttons based on your HTML
        pickup_selectors = [
            '.rc-segmented-control-button',
            'button.rc-segmented-control-button',
            'button[role="tab"]',
            'button[class*="segmented-control"]',
            '.rc-segmented-control-item button'
        ]
        
        for selector in pickup_selectors:
            try:
                print(f"Looking for pickup buttons with selector: {selector}")
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Found {len(buttons)} segmented control buttons")
                
                if len(buttons) >= 2:
                    # Usually pickup is the second button (index 1)
                    pickup_button = buttons[1]
                    print(f"Attempting to click second segmented button (pickup)")
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pickup_button)
                    time.sleep(1)
                    
                    # Try different click methods
                    click_methods = [
                        ("Regular click", lambda: pickup_button.click()),
                        ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", pickup_button)),
                        ("Action chains", lambda: ActionChains(self.driver).move_to_element(pickup_button).click().perform()),
                        ("Force click event", lambda: self.driver.execute_script("""
                            arguments[0].dispatchEvent(new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }));
                        """, pickup_button))
                    ]
                    
                    for method_name, method in click_methods:
                        try:
                            print(f"Trying {method_name}...")
                            method()
                            time.sleep(2)
                            
                            # Check if button state changed
                            button_class = pickup_button.get_attribute('class')
                            aria_checked = pickup_button.get_attribute('aria-checked')
                            
                            if 'selected' in button_class or aria_checked == 'true':
                                print(f"✓ Pickup button clicked successfully using {method_name}")
                                print(f"Button class: {button_class}")
                                print(f"Aria-checked: {aria_checked}")
                                time.sleep(3)  # Wait for pickup section to load
                                return self.handle_zip_code_input()
                            else:
                                print(f"{method_name} - no state change detected")
                        except Exception as e:
                            print(f"{method_name} failed: {e}")
                            continue
                    
                    print("All click methods failed for pickup button")
                    return False
                    
            except Exception as e:
                print(f"Selector {selector} failed: {e}")
                continue
        
        print("✗ Could not find pickup segmented control buttons")
        return False

    # STEP 8: Zip Code Input and Store Selection
    def handle_zip_code_input(self):
        if self._stopped:
            return False
        
        print("STEP 8: Zip code input and store selection...")
        
        # Based on your HTML, the exact selectors we need
        zip_selectors = [
            'input[data-autom="storelocator-searchinput"]',  # Most specific from your HTML
            'input.form-textbox-input',                      # Class from your HTML
            'input[aria-labelledby="checkout.fulfillment.pickupTab.pickup.storeLocator.searchInput_label"]',
            'input[data-autom*="storelocator"]',
            'input[placeholder*="Code or City"]',
            '.form-textbox input[type="text"]'
        ]
        
        for selector in zip_selectors:
            try:
                print(f"Trying selector: {selector}")
                zip_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                print(f"✓ Found zip input field with selector: {selector}")
                
                # Clear any existing text
                zip_input.clear()
                time.sleep(0.5)
                
                # Enter the zip code
                zip_input.send_keys(self.user_data['zip_code'])
                print(f"✓ Entered zip code: {self.user_data['zip_code']}")
                time.sleep(1)
                
                # Now look for the Apply button based on your HTML structure
                apply_selectors = [
                    'button[id="checkout.fulfillment.pickupTab.pickup.storeLocator.apply"]',  # From your HTML
                    'button.form-textbox-button',                                            # Class from HTML
                    'button[data-autom*="apply"]',
                    'button[type="button"][class*="form-textbox-button"]',
                    '.form-textbox-button',
                    'button[id*="apply"]'
                ]
                
                apply_clicked = False
                for apply_selector in apply_selectors:
                    try:
                        print(f"Looking for apply button with selector: {apply_selector}")
                        apply_btn = self.driver.find_element(By.CSS_SELECTOR, apply_selector)
                        if apply_btn.is_displayed() and apply_btn.is_enabled():
                            apply_btn.click()
                            print("✓ Apply button clicked successfully")
                            apply_clicked = True
                            break
                    except Exception as e:
                        print(f"Apply selector {apply_selector} failed: {e}")
                        continue
                
                if not apply_clicked:
                    # If no apply button found, try pressing Enter
                    print("No apply button found, trying Enter key...")
                    zip_input.send_keys(Keys.ENTER)
                    print("✓ Pressed Enter on zip input")
                
                # Wait for stores to load and then validate them
                print("Waiting for stores to load...")
                time.sleep(5)
                return self.validate_and_select_store()
                
            except Exception as e:
                print(f"Zip selector {selector} failed: {e}")
                continue
        
        print("✗ Could not find zip code input field with any selector")
        return False

    # NEW STEP 9: Validate stores and select valid one
    def validate_and_select_store(self):
        if self._stopped:
            return False
        
        print("STEP 9: Validating stores for dates 19-20-21-22...")
        
        try:
            # Wait for store list to load
            store_list = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rt-storelocator-store-group.form-selector-group"))
            )
            print("✓ Store list found")
            time.sleep(2)
            
            # Get all store items (li elements)
            store_items = store_list.find_elements(By.TAG_NAME, "li")
            print(f"Found {len(store_items)} stores to check")
            
            valid_dates = ['19', '20', '21', '22']
            
            for index, store_item in enumerate(store_items):
                try:
                    print(f"\nChecking store {index + 1}...")
                    
                    # First click on the li to load/reveal the dates
                    try:
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", store_item)
                        time.sleep(1)
                        
                        # Click the store item to reveal dates
                        store_item.click()
                        print(f"✓ Clicked on store {index + 1} to check dates")
                        
                        # Wait exactly 3 seconds as requested
                        print("Waiting 3 seconds to check dates...")
                        time.sleep(3)
                        
                    except Exception as e:
                        print(f"Failed to click store {index + 1}: {e}")
                        continue
                    
                    # Now get the text content after clicking and waiting
                    store_text = store_item.text.lower()
                    print(f"Store text after click: {store_text[:150]}...")  # First 150 chars
                    
                    # Also check the entire page content for dates (they might appear elsewhere)
                    try:
                        # Look for date elements that might have appeared after clicking
                        date_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".rs-pickup-slot, .pickup-slot, [class*='date'], [class*='time'], [id*='date'], [id*='time']")
                        
                        for date_element in date_elements:
                            date_text = date_element.text.lower()
                            store_text += " " + date_text
                            
                    except:
                        pass
                    
                    # Check if any valid dates are present
                    has_valid_date = False
                    found_dates = []
                    
                    for date in valid_dates:
                        if date in store_text:
                            has_valid_date = True
                            found_dates.append(date)
                    
                    if has_valid_date:
                        print(f"✓ Store {index + 1} has valid dates: {found_dates}")
                        print("This store is valid - proceeding to time slot selection")
                        
                        # Store is already clicked and valid, now handle the time slot dropdown
                        return self.handle_time_slot_selection()
                        
                    else:
                        print(f"✗ Store {index + 1} does not have valid dates (19-20-21-22)")
                        print("Continuing to next store...")
                        
                except Exception as e:
                    print(f"Error checking store {index + 1}: {e}")
                    continue
            
            # If we get here, no valid stores were found
            print("✗ No stores with valid dates (19-20-21-22) found")
            print("Restarting from scratch as requested...")
            return self.restart_automation()
            
        except Exception as e:
            print(f"Error in store validation: {e}")
            print("Restarting from scratch...")
            return self.restart_automation()

    # NEW STEP 10: Handle time slot dropdown selection
    def handle_time_slot_selection(self):
        if self._stopped:
            return False
        
        print("STEP 10: Handling time slot dropdown selection...")
        
        try:
            # Wait for dropdown to appear - based on your HTML structure
            dropdown_selectors = [
                'select[id="checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots.timeSlotValue"]',
                'select.form-dropdown-select',
                'select[data-autom*="pickup"]',
                '.form-dropdown select',
                'select[id*="timeSlot"]'
            ]
            
            for selector in dropdown_selectors:
                try:
                    print(f"Looking for dropdown with selector: {selector}")
                    dropdown = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    print("✓ Time slot dropdown found")
                    
                    # Get all options
                    options = dropdown.find_elements(By.TAG_NAME, "option")
                    print(f"Found {len(options)} time slot options")
                    
                    # Select first available option (skip first if it's placeholder)
                    for i, option in enumerate(options):
                        option_text = option.text.strip()
                        option_value = option.get_attribute('value')
                        
                        print(f"Option {i}: '{option_text}' (value: '{option_value}')")
                        
                        # Skip empty or placeholder options
                        if option_value and option_value != "" and option_text and "select" not in option_text.lower():
                            print(f"✓ Selecting first available option: '{option_text}'")
                            option.click()
                            time.sleep(2)
                            
                            # After selecting time slot, scroll to bottom and click continue
                            return self.scroll_and_continue()
                    
                    print("No valid time slot options found")
                    return False
                    
                except Exception as e:
                    print(f"Dropdown selector {selector} failed: {e}")
                    continue
            
            print("✗ Could not find time slot dropdown")
            return False
            
        except Exception as e:
            print(f"Error in time slot selection: {e}")
            return False

    # NEW STEP 11: Scroll to bottom and click continue button
    def scroll_and_continue(self):
        if self._stopped:
            return False
        
        print("STEP 11: Scrolling to bottom and clicking continue button...")
        
        try:
            # Scroll to 100% of the page as requested
            print("Scrolling to 100% of the page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for the continue button based on your HTML
            continue_selectors = [
                'button[id="rs-checkout-continue-button-bottom"]',  # From your HTML
                'button[data-analytics-title="Continue Button"]',   # From your HTML
                'button.large-6.small-12.rs-checkout-action-button-wrapper button',
                'button[class*="continue"]',
                '.rs-checkout-action button',
                'button[type="button"][class*="form-button"]',
                '.rs-checkout-action-button-wrapper button'
            ]
            
            for selector in continue_selectors:
                try:
                    print(f"Looking for continue button with selector: {selector}")
                    continue_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Scroll the button into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                    time.sleep(1)
                    
                    # Click the continue button
                    continue_btn.click()
                    print("✓ Continue button clicked successfully")
                    
                    print("🎉 SUCCESS - ALL STEPS COMPLETED!")
                    print("All requested steps have been executed successfully:")
                    print("✓ No Coverage selected")
                    print("✓ 2 iPhones added to bag") 
                    print("✓ Checkout clicked")
                    print("✓ Continue as guest")
                    print("✓ Pickup button clicked")
                    print("✓ Zip code entered and applied")
                    print("✓ Valid store selected (dates 19-20-21-22)")
                    print("✓ First available time slot selected")
                    print("✓ Scrolled to bottom and clicked continue")
                    
                    time.sleep(10)  # Keep browser open to see results
                    return True
                    
                except Exception as e:
                    print(f"Continue selector {selector} failed: {e}")
                    continue
            
            print("✗ Could not find continue button")
            return False
            
        except Exception as e:
            print(f"Error in scroll and continue: {e}")
            return False

    def restart_automation(self):
        """Restart the automation from the beginning"""
        try:
            print("🔄 RESTARTING AUTOMATION FROM SCRATCH...")
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        self.driver = None
        self.purchase_count = 0
        self.error_count = 0
        time.sleep(5)
        
        return self.run()

    def run_purchase_flow(self):
        if self._stopped:
            return False
        
        print(f"Starting purchase flow for iPhone {self.purchase_count + 1}...")
        
        # Scroll page a bit
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
        time.sleep(2)
        
        # Step 1: No Coverage
        if not self.click_applecare_no_coverage():
            print("Failed to select no coverage")
            return False
        
        # Step 2: Add to Bag
        if not self.add_to_bag():
            print("Failed to add to bag")
            return False
        
        # Step 3: Handle bag page (go back for 2nd iPhone or proceed)
        return self.handle_bag_page()

    def run(self):
        automation_success = False
        
        try:
            proxy_status = "WITH PROXY" if self.use_proxy else "WITHOUT PROXY"
            print(f"Process {self.process_num}: Starting simplified Apple automation {proxy_status}...")
            print(f"Product URL: {self.config.PRODUCT_URL}")
            print(f"Target: {self.max_purchases} iPhones")
            print(f"Steps: No Coverage → Add to Bag (2x) → Checkout → Guest → Pickup → Zip Code")
            
            try:
                process_email = self.get_process_email()
                print(f"Process {self.process_num}: Using email: {process_email}")
            except Exception as e:
                print(f"Process {self.process_num}: Email assignment error: {e}")
            
            print(f"Contact: {self.user_data['first_name']} {self.user_data['last_name']}")
            print(f"Zip Code: {self.user_data['zip_code']}")
            
            self.purchase_count = 0
            
            if not self.setup_driver():
                raise Exception("Failed to setup WebDriver")
            
            if self._stopped:
                print(f"Process {self.process_num}: Stopped before starting")
                return False
            
            print(f"Process {self.process_num}: Opening Apple website...")
            self.driver.get(self.config.PRODUCT_URL)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"Process {self.process_num}: Page loaded successfully")
            
            self.saved_link = self.driver.current_url
            print(f"Process {self.process_num}: Saved page URL for going back")
            
            # Start the main flow
            success = self.run_purchase_flow()
            
            if success:
                print(f"Process {self.process_num}: 🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
                automation_success = True
            else:
                print(f"Process {self.process_num}: ❌ Process failed")
            
            try:
                self.mark_email_status(success=automation_success)
            except Exception as e:
                print(f"Process {self.process_num}: Error updating email status: {e}")
            
            # Keep browser open for a moment to see results
            if automation_success:
                print("Keeping browser open for 10 seconds to see results...")
                time.sleep(10)
            
            if self.driver:
                try:
                    print(f"Process {self.process_num}: Closing browser...")
                    self.driver.quit()
                except Exception as e:
                    print(f"Process {self.process_num}: Error closing browser: {e}")
                finally:
                    self.driver = None
            
            return automation_success
            
        except KeyboardInterrupt:
            print(f"Process {self.process_num}: Automation interrupted by user")
            try:
                self.mark_email_status(success=False)
            except:
                pass
            self.stop()
            return False
            
        except Exception as e:
            print(f"Process {self.process_num}: Unexpected error: {e}")
            traceback.print_exc()
            
            try:
                self.mark_email_status(success=False)
            except:
                pass
            
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                finally:
                    self.driver = None
            
            return False
        
        finally:
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            status_text = "SUCCESS" if automation_success else "FAILED"
            print(f"Process {self.process_num}: Final status - {status_text}")


if __name__ == "__main__":
    automation = AppleAutomation()
    automation.run()