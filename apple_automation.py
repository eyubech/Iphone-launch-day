import time
import sys
import traceback
import os
import tempfile
import zipfile
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
        self.proxy_extension_path = None
        
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

    def create_proxy_extension(self):
        if not self.use_proxy:
            return None
        
        try:
            extension_dir = tempfile.mkdtemp()
            
            if hasattr(self.proxy, 'password'):
                username = f"{self.proxy.username}-session-{self.proxy.generate_session_id(self.process_num)}"
                password = self.proxy.password
            else:
                username = f"{self.proxy.username}-session-{self.proxy.generate_session_id(self.process_num)}"
                password = self.proxy.zone_id
            
            manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Proxy Auth Extension",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    }
}
"""
            
            background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{self.proxy.endpoint}",
            port: parseInt({self.proxy.port})
        }},
        bypassList: []
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
    console.log("Proxy configured");
}});

function callbackFn(details) {{
    console.log("Proxy auth required for:", details.url);
    return {{
        authCredentials: {{
            username: "{username}",
            password: "{password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

console.log("Proxy extension loaded with auth for {self.proxy.endpoint}:{self.proxy.port}");
"""
            
            with open(os.path.join(extension_dir, 'manifest.json'), 'w') as f:
                f.write(manifest_json)
            
            with open(os.path.join(extension_dir, 'background.js'), 'w') as f:
                f.write(background_js)
            
            extension_zip = tempfile.mktemp(suffix='.zip')
            with zipfile.ZipFile(extension_zip, 'w') as zf:
                zf.write(os.path.join(extension_dir, 'manifest.json'), 'manifest.json')
                zf.write(os.path.join(extension_dir, 'background.js'), 'background.js')
            
            import shutil
            shutil.rmtree(extension_dir)
            
            self.proxy_extension_path = extension_zip
            print(f"Process {self.process_num}: Created proxy extension at {extension_zip}")
            return extension_zip
            
        except Exception as e:
            print(f"Process {self.process_num}: Failed to create proxy extension: {e}")
            return None

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
        
        # Simplified proxy handling - use Chrome args instead of extension
        if self.use_proxy:
            try:
                if hasattr(self.proxy, 'password'):
                    username = f"{self.proxy.username}-session-{self.proxy.generate_session_id(self.process_num)}"
                    password = self.proxy.password
                else:
                    username = f"{self.proxy.username}-session-{self.proxy.generate_session_id(self.process_num)}"
                    password = self.proxy.zone_id
                
                proxy_server = f"http://{self.proxy.endpoint}:{self.proxy.port}"
                proxy_auth = f"{username}:{password}"
                
                options.add_argument(f"--proxy-server={proxy_server}")
                options.add_argument(f"--proxy-auth={proxy_auth}")
                print(f"Process {self.process_num}: Configured proxy via Chrome arguments")
                
            except Exception as e:
                print(f"Process {self.process_num}: Failed to configure proxy: {e}")
                print(f"Process {self.process_num}: Continuing without proxy...")
                self.use_proxy = False
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        options.add_argument("--disable-web-security")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if self.use_proxy:
                print(f"Process {self.process_num}: Testing proxy connection...")
                try:
                    self.driver.set_page_load_timeout(30)
                    self.driver.get("http://httpbin.org/ip")
                    time.sleep(3)
                    page_content = self.driver.page_source
                    if "origin" in page_content:
                        print(f"Process {self.process_num}: Proxy test successful")
                    else:
                        print(f"Process {self.process_num}: Proxy test inconclusive")
                except Exception as e:
                    print(f"Process {self.process_num}: Proxy test failed: {e}")
                    print(f"Process {self.process_num}: Continuing anyway...")
            
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
        
        if self.proxy_extension_path and os.path.exists(self.proxy_extension_path):
            try:
                os.remove(self.proxy_extension_path)
            except:
                pass

    def click_applecare_no_coverage(self):
        if self._stopped:
            return False
        
        print("STEP 1: Looking for AppleCare no coverage option...")
        
        try:
            radios = self.driver.find_elements(By.NAME, "applecare-options")
            if len(radios) >= 3:
                print(f"Found {len(radios)} AppleCare options, clicking third option (no coverage)")
                radios[2].click()
                print("No coverage selected successfully")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
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
                print("No coverage selected successfully")
                time.sleep(2)
                return True
            except:
                continue
        
        print("Could not find AppleCare no coverage option")
        return False

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
                print(f"iPhone {self.purchase_count + 1} added to bag successfully")
                time.sleep(3)
                return True
            except:
                continue
        
        print("Could not find add to bag button")
        return False

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
                
                return self.run_purchase_flow()
                
            except Exception as e:
                print(f"Error navigating back to product page: {e}")
                return False
        else:
            print("STEP 3: Both iPhones added, proceeding to checkout")
            return self.proceed_to_checkout()

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
                print("Proceed to checkout clicked successfully")
                time.sleep(3)
                return self.handle_checkout_flow()
            except:
                continue
        
        print("Could not find proceed to checkout button")
        return False

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
                print("Checkout button clicked successfully")
                time.sleep(3)
                return self.handle_guest_login()
            except:
                continue
        
        print("Could not find checkout button")
        return False

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
                print("Guest login clicked successfully")
                time.sleep(5)
                return self.handle_pickup_section()
            except:
                continue
        
        print("Could not find guest login button")
        return False

    def handle_pickup_section(self):
        if self._stopped:
            return False
        
        print("STEP 7: Looking for pickup button (segmented control)...")
        time.sleep(5)
        
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
                    pickup_button = buttons[1]
                    print(f"Attempting to click second segmented button (pickup)")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pickup_button)
                    time.sleep(1)
                    
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
                            
                            button_class = pickup_button.get_attribute('class')
                            aria_checked = pickup_button.get_attribute('aria-checked')
                            
                            if 'selected' in button_class or aria_checked == 'true':
                                print(f"Pickup button clicked successfully using {method_name}")
                                print(f"Button class: {button_class}")
                                print(f"Aria-checked: {aria_checked}")
                                time.sleep(3)
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
        
        print("Could not find pickup segmented control buttons")
        return False

    def handle_zip_code_input(self):
        if self._stopped:
            return False
        
        print("STEP 8: Zip code input and store selection...")
        
        zip_selectors = [
            'input[data-autom="storelocator-searchinput"]',
            'input.form-textbox-input',
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
                
                print(f"Found zip input field with selector: {selector}")
                
                zip_input.clear()
                time.sleep(0.5)
                
                zip_input.send_keys(self.user_data['zip_code'])
                print(f"Entered zip code: {self.user_data['zip_code']}")
                time.sleep(1)
                
                apply_selectors = [
                    'button[id="checkout.fulfillment.pickupTab.pickup.storeLocator.apply"]',
                    'button.form-textbox-button',
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
                            print("Apply button clicked successfully")
                            apply_clicked = True
                            break
                    except Exception as e:
                        print(f"Apply selector {apply_selector} failed: {e}")
                        continue
                
                if not apply_clicked:
                    print("No apply button found, trying Enter key...")
                    zip_input.send_keys(Keys.ENTER)
                    print("Pressed Enter on zip input")
                
                print("Waiting for stores to load...")
                time.sleep(5)
                return self.validate_and_select_store()
                
            except Exception as e:
                print(f"Zip selector {selector} failed: {e}")
                continue
        
        print("Could not find zip code input field with any selector")
        return False

    def validate_and_select_store(self):
        if self._stopped:
            return False
        
        print("STEP 9: Validating stores for dates 19-20-21-22...")
        
        try:
            store_list = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rt-storelocator-store-group.form-selector-group"))
            )
            print("Store list found")
            time.sleep(2)
            
            store_items = store_list.find_elements(By.TAG_NAME, "li")
            print(f"Found {len(store_items)} stores to check")
            
            valid_dates = ['19', '20', '21', '22']
            
            for index, store_item in enumerate(store_items):
                try:
                    print(f"\nChecking store {index + 1}...")
                    
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", store_item)
                        time.sleep(1)
                        
                        store_item.click()
                        print(f"Clicked on store {index + 1} to check dates")
                        
                        print("Waiting 3 seconds to check dates...")
                        time.sleep(6)
                        
                    except Exception as e:
                        print(f"Failed to click store {index + 1}: {e}")
                        continue
                    
                    store_text = store_item.text.lower()
                    print(f"Store text after click: {store_text[:150]}...")
                    
                    try:
                        date_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".rs-pickup-slot, .pickup-slot, [class*='date'], [class*='time'], [id*='date'], [id*='time']")
                        
                        for date_element in date_elements:
                            date_text = date_element.text.lower()
                            store_text += " " + date_text
                            
                    except:
                        pass
                    
                    has_valid_date = False
                    found_dates = []
                    
                    for date in valid_dates:
                        if date in store_text:
                            has_valid_date = True
                            found_dates.append(date)
                    
                    if has_valid_date:
                        print(f"Store {index + 1} has valid dates: {found_dates}")
                        print("This store is valid - proceeding to time slot selection")
                        
                        return self.handle_time_slot_selection()
                        
                    else:
                        print(f"Store {index + 1} does not have valid dates (19-20-21-22)")
                        print("Continuing to next store...")
                        
                except Exception as e:
                    print(f"Error checking store {index + 1}: {e}")
                    continue
            
            print("No stores with valid dates (19-20-21-22) found")
            print("Restarting from scratch as requested...")
            return self.restart_automation()
            
        except Exception as e:
            print(f"Error in store validation: {e}")
            print("Restarting from scratch...")
            return self.restart_automation()

    def handle_time_slot_selection(self):
        if self._stopped:
            return False
        
        print("STEP 10: Handling time slot dropdown selection...")
        
        try:
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
                    
                    print("Time slot dropdown found")
                    
                    options = dropdown.find_elements(By.TAG_NAME, "option")
                    print(f"Found {len(options)} time slot options")
                    
                    for i, option in enumerate(options):
                        option_text = option.text.strip()
                        option_value = option.get_attribute('value')
                        
                        print(f"Option {i}: '{option_text}' (value: '{option_value}')")
                        
                        if option_value and option_value != "" and option_text and "select" not in option_text.lower():
                            print(f"Selecting first available option: '{option_text}'")
                            option.click()
                            time.sleep(2)
                            
                            return self.scroll_and_continue()
                    
                    print("No valid time slot options found")
                    return False
                    
                except Exception as e:
                    print(f"Dropdown selector {selector} failed: {e}")
                    continue
            
            print("Could not find time slot dropdown")
            return False
            
        except Exception as e:
            print(f"Error in time slot selection: {e}")
            return False

    def scroll_and_continue(self):
        if self._stopped:
            return False
        
        print("STEP 11: Scrolling to bottom and clicking continue button...")
        
        try:
            print("Scrolling to 100% of the page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            continue_selectors = [
                'button[id="rs-checkout-continue-button-bottom"]',
                'button[data-analytics-title="Continue Button"]',
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
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_btn)
                    time.sleep(1)
                    
                    continue_btn.click()
                    print("Continue button clicked successfully")
                    
                    print("Proceeding to form filling...")
                    time.sleep(3)
                    return self.fill_contact_forms()
                    
                except Exception as e:
                    print(f"Continue selector {selector} failed: {e}")
                    continue
            
            print("Could not find continue button")
            return False
            
        except Exception as e:
            print(f"Error in scroll and continue: {e}")
            return False

    def fill_contact_forms(self):
        if self._stopped:
            return False
        
        print("STEP 12: Filling contact forms...")
        
        try:
            print("Waiting for form to load...")
            time.sleep(3)
            
            # Third party pickup button
            print("Looking for third party pickup option...")
            third_party_selectors = [
                'button[data-autom="thirdPartyPickup"]',
                'input[data-autom="thirdPartyPickup"]',
                '.rc-segmented-control-item button[data-autom="thirdPartyPickup"]',
                'button[role="radio"][data-autom="thirdPartyPickup"]',
                '.rc-segmented-control-item[data-autom="thirdPartyPickup"]'
            ]
            
            third_party_clicked = False
            for selector in third_party_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    print("Third party pickup selected")
                    third_party_clicked = True
                    time.sleep(2)
                    break
                except:
                    continue
            
            if not third_party_clicked:
                print("Could not find third party pickup option, continuing...")
            
            # Fill first name
            print("Filling first name...")
            first_name_selectors = [
                'input[id="checkout.pickupContact.selfPickupContact.selfContact.address.firstName"]',
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.firstName"]',
                'input[name="firstName"]',
                'input[data-autom="form-field-firstName"]'
            ]
            
            for selector in first_name_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['first_name'])
                    print(f"First name filled: {self.user_data['first_name']}")
                    break
                except:
                    continue
            
            # Fill last name
            print("Filling last name...")
            last_name_selectors = [
                'input[id="checkout.pickupContact.selfPickupContact.selfContact.address.lastName"]',
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.lastName"]',
                'input[name="lastName"]',
                'input[data-autom="form-field-lastName"]'
            ]
            
            for selector in last_name_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['last_name'])
                    print(f"Last name filled: {self.user_data['last_name']}")
                    break
                except:
                    continue
            
            # Fill email
            print("Filling email...")
            email_selectors = [
                'input[id="checkout.pickupContact.selfPickupContact.selfContact.address.emailAddress"]',
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.emailAddress"]',
                'input[name="emailAddress"]',
                'input[type="email"]',
                'input[data-autom="form-field-emailAddress"]'
            ]
            
            for selector in email_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['email'])
                    print(f"Email filled: {self.user_data['email']}")
                    break
                except:
                    continue
            
            # Fill phone
            print("Filling phone...")
            phone_selectors = [
                'input[id="checkout.pickupContact.selfPickupContact.selfContact.address.fullDaytimePhone"]',
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.fullDaytimePhone"]',
                'input[name="fullDaytimePhone"]',
                'input[type="tel"]',
                'input[data-autom="form-field-fullDaytimePhone"]'
            ]
            
            for selector in phone_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['phone'])
                    print(f"Phone filled: {self.user_data['phone']}")
                    break
                except:
                    continue
            
            print("Scrolling to check for billing contact section...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Fill billing contact email (same as above)
            print("Filling billing contact email...")
            billing_email_selectors = [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.billingContact.address.emailAddress"]',
                'input[name="emailAddress"][type="email"]',
                'input[data-autom="form-field-emailAddress"]'
            ]
            
            for selector in billing_email_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['email'])
                    print(f"Billing email filled: {self.user_data['email']}")
                    break
                except:
                    continue
            
            # Fill billing contact phone (same as above)
            print("Filling billing contact phone...")
            billing_phone_selectors = [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.billingContact.address.fullDaytimePhone"]',
                'input[name="fullDaytimePhone"][type="tel"]',
                'input[data-autom="form-field-fullDaytimePhone"]'
            ]
            
            for selector in billing_phone_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(self.user_data['phone'])
                    print(f"Billing phone filled: {self.user_data['phone']}")
                    break
                except:
                    continue
            
            # Check notification checkbox if exists
            print("Looking for notification checkbox...")
            checkbox_selectors = [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.acceptTextNotification"]',
                'input[type="checkbox"]',
                '.form-checkbox input'
            ]
            
            for selector in checkbox_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if not element.is_selected():
                        element.click()
                        print("Notification checkbox checked")
                    break
                except:
                    continue
            
            print("Scrolling to bottom to find continue button...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Continue to payment
            print("Looking for continue to payment button...")
            continue_payment_selectors = [
                'button[data-autom="continue-button-label"]',
                'button[id="rs-checkout-continue-button-bottom"]',
                '.rs-checkout-action button',
                'button[class*="form-button"]',
                'button[type="button"][class*="continue"]'
            ]
            
            for selector in continue_payment_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    element.click()
                    print("Continue to payment clicked successfully")
                    
                    time.sleep(3)
                    return self.handle_payment_form()
                    
                except Exception as e:
                    print(f"Continue payment selector {selector} failed: {e}")
                    continue
            
            print("Could not find continue to payment button")
            return False
            
        except Exception as e:
            print(f"Error in form filling: {e}")
            return False

    def handle_payment_form(self):
        if self._stopped:
            return False
        
        print("STEP 13: Handling payment form...")
        
        try:
            print("Waiting for payment form to load...")
            time.sleep(5)
            
            # Select credit card payment option with multiple methods
            print("Selecting credit card payment...")
            credit_selectors = [
                'input[id="checkout.billing.billingoptions.credit"]',
                'input[name="checkout.billing.billingoptions"][value="CREDIT"]',
                'input[type="radio"][value="CREDIT"]',
                'label[for="checkout.billing.billingoptions.credit"]'
            ]
            
            credit_clicked = False
            for selector in credit_selectors:
                try:
                    print(f"Trying credit card selector: {selector}")
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # Try multiple click methods
                    click_methods = [
                        ("Regular click", lambda: element.click()),
                        ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", element)),
                        ("Force click", lambda: self.driver.execute_script("""
                            arguments[0].checked = true;
                            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                        """, element))
                    ]
                    
                    for method_name, method in click_methods:
                        try:
                            print(f"Trying {method_name} on credit card option...")
                            method()
                            time.sleep(2)
                            
                            # Check if it's selected
                            if element.is_selected() or element.get_attribute('checked'):
                                print(f"Credit card option selected successfully using {method_name}")
                                credit_clicked = True
                                break
                        except Exception as e:
                            print(f"{method_name} failed: {e}")
                            continue
                    
                    if credit_clicked:
                        break
                        
                except Exception as e:
                    print(f"Credit selector {selector} failed: {e}")
                    continue
            
            if not credit_clicked:
                print("Failed to select credit card option, trying label click...")
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, 'label[for="checkout.billing.billingoptions.credit"]')
                    label.click()
                    print("Credit card label clicked")
                    credit_clicked = True
                except:
                    print("Label click also failed")
            
            if credit_clicked:
                print("Waiting 10 seconds after credit card selection as requested...")
                time.sleep(10)
            else:
                print("Warning: Could not select credit card option, continuing anyway...")
                time.sleep(3)
            
            # Get card data from user_data or config defaults
            card_number = getattr(self, 'card_data', {}).get('card_number', self.config.DEFAULT_VALUES['credit_card'])
            expiry_date = getattr(self, 'card_data', {}).get('expiry_date', self.config.DEFAULT_VALUES['expiry_date'])
            cvc = getattr(self, 'card_data', {}).get('cvc', self.config.DEFAULT_VALUES['cvc'])
            
            # Fill card number
            print("Filling card number...")
            card_number_selectors = [
                'input[id*="cardNumber"]',
                'input[name*="cardNumber"]',
                'input[data-autom*="card-number"]',
                'input[placeholder*="Card number"]',
                'input[aria-labelledby*="cardNumber"]'
            ]
            
            for selector in card_number_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    element.clear()
                    element.send_keys(card_number)
                    print(f"Card number filled: {card_number[:4]}****{card_number[-4:]}")
                    break
                except Exception as e:
                    print(f"Card number selector {selector} failed: {e}")
                    continue
            
            # Fill expiry date
            print("Filling expiry date...")
            expiry_selectors = [
                'input[id*="expiration"]',
                'input[name*="expiry"]',
                'input[data-autom*="expiry"]',
                'input[placeholder*="MM/YY"]',
                'input[aria-labelledby*="expiry"]'
            ]
            
            for selector in expiry_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(expiry_date)
                    print(f"Expiry date filled: {expiry_date}")
                    break
                except Exception as e:
                    print(f"Expiry selector {selector} failed: {e}")
                    continue
            
            # Fill CVC
            print("Filling CVC...")
            cvc_selectors = [
                'input[id*="securityCode"]',
                'input[name*="cvc"]',
                'input[data-autom*="security"]',
                'input[placeholder*="CVC"]',
                'input[aria-labelledby*="security"]'
            ]
            
            for selector in cvc_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(cvc)
                    print(f"CVC filled: ***")
                    break
                except Exception as e:
                    print(f"CVC selector {selector} failed: {e}")
                    continue
            
            # Scroll down 35% as requested
            print("Scrolling down 35% of the page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.35);")
            time.sleep(2)
            
            # Get billing data from card_data or fallback to user_data
            billing_info = getattr(self, 'card_data', {}).get('billing_info', {})
            first_name = billing_info.get('first_name', self.user_data['first_name'])
            last_name = billing_info.get('last_name', self.user_data['last_name'])
            street_address = billing_info.get('street_address', self.config.DEFAULT_VALUES['street_address'])
            postal_code = billing_info.get('postal_code', self.config.DEFAULT_VALUES['postal_code'])
            
            # Fill billing first name
            print("Filling billing first name...")
            billing_first_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.firstName"]',
                'input[name*="billingAddress"][name*="firstName"]',
                'input[data-autom*="billing-first-name"]'
            ]
            
            for selector in billing_first_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(first_name)
                    print(f"Billing first name filled: {first_name}")
                    break
                except Exception as e:
                    print(f"Billing first name selector {selector} failed: {e}")
                    continue
            
            # Fill billing last name
            print("Filling billing last name...")
            billing_last_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.lastName"]',
                'input[name*="billingAddress"][name*="lastName"]',
                'input[data-autom*="billing-last-name"]'
            ]
            
            for selector in billing_last_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(last_name)
                    print(f"Billing last name filled: {last_name}")
                    break
                except Exception as e:
                    print(f"Billing last name selector {selector} failed: {e}")
                    continue
            
            # Fill billing street address
            print("Filling billing street address...")
            billing_street_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.street"]',
                'input[name*="billingAddress"][name*="street"]',
                'input[data-autom*="billing-street"]'
            ]
            
            for selector in billing_street_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(street_address)
                    print(f"Billing street filled: {street_address}")
                    break
                except Exception as e:
                    print(f"Billing street selector {selector} failed: {e}")
                    continue
            
            # Fill billing postal code
            print("Filling billing postal code...")
            billing_postal_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.zipLookup.postalCode"]',
                'input[name*="billingAddress"][name*="postal"]',
                'input[data-autom*="billing-postal"]'
            ]
            
            for selector in billing_postal_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(postal_code)
                    print(f"Billing postal code filled: {postal_code}")
                    break
                except Exception as e:
                    print(f"Billing postal selector {selector} failed: {e}")
                    continue
            
            print("Waiting 5 seconds as requested...")
            time.sleep(5)
            
            print("STEP 14: Scrolling 100% and clicking continue...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Click continue button
            continue_selectors = [
                'button[id="rs-checkout-continue-button-bottom"]',
                'button[data-analytics-title="Continue Button"]',
                'button.form-button[data-analytics-title="Continue Button"]',
                '.rs-checkout-action button',
                'button[class*="continue"]'
            ]
            
            continue_clicked = False
            for selector in continue_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    element.click()
                    print("Continue button clicked successfully")
                    continue_clicked = True
                    time.sleep(3)
                    break
                except Exception as e:
                    print(f"Continue selector {selector} failed: {e}")
                    continue
            
            if not continue_clicked:
                print("Could not find continue button")
                return False
            
            return self.handle_final_order()
            
        except Exception as e:
            print(f"Error in payment form handling: {e}")
            return False

    def handle_final_order(self):
        if self._stopped:
            return False
        
        print("STEP 15: Final order page - scrolling 100% and clicking order...")
        
        try:
            print("Waiting for order page to load...")
            time.sleep(5)
            
            # Scroll to 100% of the page
            print("Scrolling to 100% of the page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Click order button
            order_selectors = [
                'button[id="rs-checkout-continue-button-bottom"]',
                'button[data-analytics-title="Place Order"]',
                'button[data-analytics-title="Order"]',
                '.rs-checkout-action button',
                'button[class*="order"]',
                'button[type="button"][class*="form-button"]'
            ]
            
            order_clicked = False
            for selector in order_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    element.click()
                    print("Order button clicked successfully")
                    order_clicked = True
                    break
                except Exception as e:
                    print(f"Order selector {selector} failed: {e}")
                    continue
            
            if not order_clicked:
                print("Could not find order button")
                return False
            
            print("Waiting 15 seconds before finishing as requested...")
            time.sleep(15)
            
            print("ULTIMATE SUCCESS - COMPLETE AUTOMATION FINISHED!")
            print("All automation steps completed successfully:")
            print("1. No Coverage selected")
            print("2. 2 iPhones added to bag")
            print("3. Checkout process completed")
            print("4. Guest login completed")
            print("5. Pickup option selected")
            print("6. Zip code entered and store selected")
            print("7. Time slot selected")
            print("8. Contact forms filled")
            print("9. Payment form filled")
            print("10. Continue clicked")
            print("11. Order placed")
            print("AUTOMATION CYCLE COMPLETE - READY TO RESTART")
            
            return True
            
        except Exception as e:
            print(f"Error in final order handling: {e}")
            return False
            
        except Exception as e:
            print(f"Error in payment form handling: {e}")
            return False
            
            # Get card data from user_data or config defaults
            card_number = getattr(self, 'card_data', {}).get('card_number', self.config.DEFAULT_VALUES['credit_card'])
            expiry_date = getattr(self, 'card_data', {}).get('expiry_date', self.config.DEFAULT_VALUES['expiry_date'])
            cvc = getattr(self, 'card_data', {}).get('cvc', self.config.DEFAULT_VALUES['cvc'])
            
            # Fill card number
            print("Filling card number...")
            card_number_selectors = [
                'input[id*="cardNumber"]',
                'input[name*="cardNumber"]',
                'input[data-autom*="card-number"]',
                'input[placeholder*="Card number"]'
            ]
            
            for selector in card_number_selectors:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(card_number)
                    print(f"Card number filled: {card_number[:4]}****{card_number[-4:]}")
                    break
                except Exception as e:
                    print(f"Card number selector {selector} failed: {e}")
                    continue
            
            # Fill expiry date
            print("Filling expiry date...")
            expiry_selectors = [
                'input[id*="expiration"]',
                'input[name*="expiry"]',
                'input[data-autom*="expiry"]',
                'input[placeholder*="MM/YY"]'
            ]
            
            for selector in expiry_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(expiry_date)
                    print(f"Expiry date filled: {expiry_date}")
                    break
                except Exception as e:
                    print(f"Expiry selector {selector} failed: {e}")
                    continue
            
            # Fill CVC
            print("Filling CVC...")
            cvc_selectors = [
                'input[id*="securityCode"]',
                'input[name*="cvc"]',
                'input[data-autom*="security"]',
                'input[placeholder*="CVC"]'
            ]
            
            for selector in cvc_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(cvc)
                    print(f"CVC filled: ***")
                    break
                except Exception as e:
                    print(f"CVC selector {selector} failed: {e}")
                    continue
            
            # Scroll down 35% as requested
            print("Scrolling down 35% of the page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.35);")
            time.sleep(2)
            
            # Get billing data from card_data or fallback to user_data
            billing_info = getattr(self, 'card_data', {}).get('billing_info', {})
            first_name = billing_info.get('first_name', self.user_data['first_name'])
            last_name = billing_info.get('last_name', self.user_data['last_name'])
            street_address = billing_info.get('street_address', self.config.DEFAULT_VALUES['street_address'])
            postal_code = billing_info.get('postal_code', self.config.DEFAULT_VALUES['postal_code'])
            
            # Fill billing first name
            print("Filling billing first name...")
            billing_first_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.firstName"]',
                'input[name*="billingAddress"][name*="firstName"]',
                'input[data-autom*="billing-first-name"]'
            ]
            
            for selector in billing_first_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(first_name)
                    print(f"Billing first name filled: {first_name}")
                    break
                except Exception as e:
                    print(f"Billing first name selector {selector} failed: {e}")
                    continue
            
            # Fill billing last name
            print("Filling billing last name...")
            billing_last_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.lastName"]',
                'input[name*="billingAddress"][name*="lastName"]',
                'input[data-autom*="billing-last-name"]'
            ]
            
            for selector in billing_last_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(last_name)
                    print(f"Billing last name filled: {last_name}")
                    break
                except Exception as e:
                    print(f"Billing last name selector {selector} failed: {e}")
                    continue
            
            # Fill billing street address
            print("Filling billing street address...")
            billing_street_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.street"]',
                'input[name*="billingAddress"][name*="street"]',
                'input[data-autom*="billing-street"]'
            ]
            
            for selector in billing_street_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(street_address)
                    print(f"Billing street filled: {street_address}")
                    break
                except Exception as e:
                    print(f"Billing street selector {selector} failed: {e}")
                    continue
            
            # Fill billing postal code
            print("Filling billing postal code...")
            billing_postal_selectors = [
                'input[id="checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.zipLookup.postalCode"]',
                'input[name*="billingAddress"][name*="postal"]',
                'input[data-autom*="billing-postal"]'
            ]
            
            for selector in billing_postal_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.clear()
                    element.send_keys(postal_code)
                    print(f"Billing postal code filled: {postal_code}")
                    break
                except Exception as e:
                    print(f"Billing postal selector {selector} failed: {e}")
                    continue
            
            print("Waiting 5 seconds as requested...")
            time.sleep(5)
            
            print("COMPLETE SUCCESS - ALL AUTOMATION STEPS COMPLETED!")
            print("Payment form filled successfully:")
            print("Credit card option selected")
            print("Card number filled")
            print("Expiry date filled")
            print("CVC filled")
            print("Billing first name filled")
            print("Billing last name filled")
            print("Billing street address filled")
            print("Billing postal code filled")
            print("All form fields completed - automation finished")
            
            time.sleep(15)
            return True
            
        except Exception as e:
            print(f"Error in payment form handling: {e}")
            return False

    def restart_automation(self):
        try:
            print("RESTARTING AUTOMATION FROM SCRATCH...")
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
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
        time.sleep(2)
        
        if not self.click_applecare_no_coverage():
            print("Failed to select no coverage")
            return False
        
        if not self.add_to_bag():
            print("Failed to add to bag")
            return False
        
        return self.handle_bag_page()

    def run(self):
        automation_success = False
        
        try:
            proxy_status = "WITH PROXY" if self.use_proxy else "WITHOUT PROXY"
            print(f"Process {self.process_num}: Starting Apple automation {proxy_status}...")
            print(f"Product URL: {self.config.PRODUCT_URL}")
            print(f"Target: {self.max_purchases} iPhones")
            
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
            
            print(f"Process {self.process_num}: Opening website...")
            self.driver.get(self.config.PRODUCT_URL)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"Process {self.process_num}: Page loaded successfully")
            
            self.saved_link = self.driver.current_url
            print(f"Process {self.process_num}: Saved page URL for going back")
            
            success = self.run_purchase_flow()
            
            if success:
                print(f"Process {self.process_num}: ALL STEPS COMPLETED SUCCESSFULLY!")
                automation_success = True
            else:
                print(f"Process {self.process_num}: Process failed")
            
            try:
                self.mark_email_status(success=automation_success)
            except Exception as e:
                print(f"Process {self.process_num}: Error updating email status: {e}")
            
            if automation_success:
                print("Keeping browser open for 10 seconds to see results...")
                time.sleep(10)
            
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
            
            return False
        
        finally:
            self.stop()
            status_text = "SUCCESS" if automation_success else "FAILED"
            print(f"Process {self.process_num}: Final status - {status_text}")


if __name__ == "__main__":
    automation = AppleAutomation()
    automation.run()