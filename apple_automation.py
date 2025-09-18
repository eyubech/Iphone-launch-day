import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import Config


class AppleAutomation:
    def __init__(self, card_data=None, person_data=None, settings_data=None, user_data=None):
        self.config = Config()
        self.driver = None
        self._stopped = False
        self.purchase_count = 0
        self.max_purchases = 2
        self.saved_link = ''
        
        if card_data and person_data and settings_data:
            self.user_data = self._combine_automation_data(card_data, person_data, settings_data)
        elif user_data:
            self.user_data = user_data
        else:
            self.user_data = self.config.DEFAULT_VALUES
            
    def _combine_automation_data(self, card_data, person_data, settings_data):
        user_info = card_data.get('user_info', {})
        billing_info = card_data.get('billing_info', {})
        
        return {
            'zip_code': settings_data['zip_code'],
            'street_address': settings_data['street_address'],
            'postal_code': settings_data['postal_code'],
            'first_name': user_info.get('first_name', person_data['first_name']),
            'last_name': user_info.get('last_name', person_data['last_name']),
            'email': user_info.get('email', person_data['email']),
            'phone': user_info.get('phone', person_data['phone']),
            'credit_card': card_data['card_number'],
            'expiry_date': card_data['expiry_date'],
            'cvc': card_data['cvc'],
            'billing_first_name': billing_info.get('first_name', user_info.get('first_name', person_data['first_name'])),
            'billing_last_name': billing_info.get('last_name', user_info.get('last_name', person_data['last_name'])),
            'billing_street_address': billing_info.get('street_address', settings_data['street_address']),
            'billing_postal_code': billing_info.get('postal_code', settings_data['postal_code'])
        }
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        for option in self.config.BROWSER_OPTIONS:
            options.add_argument(option)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def stop(self):
        self._stopped = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def click_element(self, selector, element_name, timeout=10):
        if self._stopped:
            return False
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"✓ {element_name} clicked successfully")
            return True
        except Exception as e:
            print(f"✗ Could not find {element_name}: {str(e)}")
            return False

    def click_applecare_no_coverage(self):
        if self._stopped:
            return False
        
        print("Looking for AppleCare no coverage option...")
        
        methods = [
            lambda: self._click_applecare_by_name(),
            lambda: self._click_applecare_by_selector(),
            lambda: self._click_applecare_by_text()
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"Trying method {i} for AppleCare...")
            if method():
                return True
                
        print("Could not find AppleCare no coverage option")
        return False
    
    def _click_applecare_by_name(self):
        try:
            radios = self.driver.find_elements(By.NAME, "applecare-options")
            if len(radios) >= 3:
                print(f"Found {len(radios)} AppleCare options, clicking third option (no coverage)")
                radios[2].click()
                time.sleep(1)
                return True
        except Exception as e:
            print(f"Method 1 failed: {e}")
        return False
    
    def _click_applecare_by_selector(self):
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
                time.sleep(1)
                return True
            except:
                continue
        return False
    
    def _click_applecare_by_text(self):
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'no coverage') or contains(text(), 'No coverage') or contains(text(), 'No AppleCare')]")
            for element in elements:
                try:
                    radio = element.find_element(By.XPATH, ".//input[@type='radio'] | ./preceding-sibling::input[@type='radio'] | ./following-sibling::input[@type='radio']")
                    radio.click()
                    time.sleep(1)
                    return True
                except:
                    continue
        except:
            pass
        return False

    def add_to_bag(self):
        if self._stopped:
            return False
        
        print("Clicking add to bag...")
        selectors = [
            'button[name="add-to-cart"]',
            'button[data-autom="add-to-cart"]',
            '.as-purchaseinfo-button button',
            'form button[type="submit"]',
            'button[class*="add-to-cart"]',
            '.button[data-autom="add-to-cart"]'
        ]
        
        for selector in selectors:
            if self.click_element(selector, "Add to Bag"):
                return True
        
        print("Could not find add to bag button")
        return False

    def handle_bag_page(self):
        if self._stopped:
            return False
            
        print("Waiting for bag page to load...")
        time.sleep(3)
        
        self.purchase_count += 1
        print(f"✓ iPhone {self.purchase_count} added to bag")
        
        if self.purchase_count < self.max_purchases:
            print(f"Going back for iPhone {self.purchase_count + 1}...")
            time.sleep(2)
            self.driver.get(self.saved_link)
            time.sleep(3)
            return self.run_purchase_flow()
        else:
            print("All iPhones added, proceeding to checkout")
            return self.proceed_to_checkout()

    def proceed_to_checkout(self):
        if self._stopped:
            return False
        
        print("Looking for checkout button...")
        proceed_selectors = [
            'button[name="proceed"]',
            'button[data-autom="proceed"]',
            '.button.button-block[data-autom="proceed"]',
            'form button[type="submit"]',
            'button[class*="button-block"]'
        ]
        
        for selector in proceed_selectors:
            if self.click_element(selector, "Proceed to Checkout"):
                time.sleep(3)
                return self.handle_checkout_flow()
        
        print("Could not find proceed button")
        return False

    def handle_checkout_flow(self):
        if self._stopped:
            return False
        
        print("Handling checkout flow...")
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
            if self.click_element(selector, "Checkout"):
                time.sleep(3)
                return self.handle_guest_login()
        
        print("Could not find checkout button")
        return False

    def handle_guest_login(self):
        if self._stopped:
            return False
        
        print("Handling guest login...")
        guest_selectors = [
            'button[data-autom="guest-checkout-btn"]',
            'button[id="signin.guestLogin.guestLogin"]',
            '.form-button[data-autom="guest-checkout-btn"]',
            'button[class*="guest-checkout"]',
            '.rs-sign-in-sidebar button',
            'button[type="button"][class*="form-button"]'
        ]
        
        for selector in guest_selectors:
            if self.click_element(selector, "Continue as Guest"):
                time.sleep(3)
                return self.continue_after_guest_login()
        
        print("Could not find guest login button")
        return False

    def click_element_reliably(self, element, description="element"):
        methods = [
            ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains click", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
            ("Regular click", lambda: element.click()),
            ("Send ENTER key", lambda: element.send_keys(Keys.RETURN)),
            ("Send SPACE key", lambda: element.send_keys(Keys.SPACE))
        ]
        
        for method_name, method in methods:
            try:
                print(f"Trying {method_name} on {description}...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                method()
                print(f"Successfully clicked {description} using {method_name}")
                return True
            except Exception as e:
                print(f"{method_name} failed: {e}")
                continue
        
        print(f"All click methods failed for {description}")
        return False

    def wait_and_click_no_coverage(self):
        print("Looking for no coverage option...")
        
        try:
            print("Trying exact ID: applecare-selector-no-applecare-option")
            element = self.driver.find_element(By.ID, "applecare-selector-no-applecare-option")
            if element.is_displayed():
                print("Found element with exact ID, trying multiple click methods...")
                if self.click_and_verify_selection(element, "no applecare radio input"):
                    return True
        except Exception as e:
            print(f"Exact ID failed: {e}")
        
        try:
            print("Trying label for no applecare option")
            label = self.driver.find_element(By.CSS_SELECTOR, "label[for='applecare-selector-no-applecare-option']")
            if label.is_displayed():
                print("Found label, trying click...")
                if self.click_and_verify_selection(label, "no applecare label"):
                    return True
        except Exception as e:
            print(f"Label click failed: {e}")
        
        try:
            print("Searching all radio inputs...")
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            print(f"Found {len(radios)} radio inputs")
            
            for i, radio in enumerate(radios):
                try:
                    radio_id = radio.get_attribute('id')
                    radio_value = radio.get_attribute('value')
                    radio_name = radio.get_attribute('name')
                    radio_autom = radio.get_attribute('data-autom')
                    print(f"Radio {i+1}: id='{radio_id}', value='{radio_value}', name='{radio_name}', data-autom='{radio_autom}'")
                    
                    if radio.is_displayed() and (
                        (radio_id and 'no' in radio_id.lower() and 'applecare' in radio_id.lower()) or
                        (radio_value and 'no' in radio_value.lower()) or
                        (radio_autom and 'noapplecare' in radio_autom.lower())
                    ):
                        print(f"Found matching radio: {radio_id}")
                        if self.click_and_verify_selection(radio, f"radio {i+1}"):
                            return True
                except Exception as e:
                    print(f"Error checking radio {i+1}: {e}")
        except Exception as e:
            print(f"Radio search failed: {e}")
        
        print("Could not find or successfully click 'no coverage' option")
        return False

    def click_and_verify_selection(self, element, description):
        click_methods = [
            ("Regular click", lambda: element.click()),
            ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", element)),
            ("ActionChains click", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
            ("Force JavaScript", lambda: self.driver.execute_script("arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change'));", element)),
            ("Double click", lambda: ActionChains(self.driver).double_click(element).perform()),
            ("Send SPACE key", lambda: element.send_keys(Keys.SPACE))
        ]
        
        for method_name, method in click_methods:
            try:
                print(f"Trying {method_name} on {description}...")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                
                initial_checked = element.get_attribute('checked')
                print(f"Initial checked state: {initial_checked}")
                
                method()
                time.sleep(1)
                
                final_checked = element.get_attribute('checked')
                print(f"Final checked state: {final_checked}")
                
                if final_checked == 'true' or final_checked == True:
                    print(f"Successfully selected {description} using {method_name}")
                    return True
                else:
                    print(f"{method_name} clicked but element not selected")
                    
            except Exception as e:
                print(f"{method_name} failed: {e}")
                continue
        
        print(f"All click methods failed to select {description}")
        return False

    def continue_after_guest_login(self):
        if self._stopped:
            return False
        
        print("Continuing after guest login - enhanced from direct-order.py...")
        time.sleep(8)
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".rc-segmented-control-button"))
            )
            print("Segmented control buttons are now present")
        except:
            print("Timeout waiting for buttons, continuing anyway...")
        
        print("Direct approach: clicking second rc-segmented-control-button...")
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, ".rc-segmented-control-button")
            print(f"Found {len(buttons)} rc-segmented-control-button elements")
            
            if len(buttons) >= 2:
                button = buttons[1]
                print(f"Attempting to click second button (index 1)")
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                
                initial_class = button.get_attribute('class')
                print(f"Initial button class: {initial_class}")
                
                click_approaches = [
                    ("Regular click", lambda: button.click()),
                    ("JavaScript click", lambda: self.driver.execute_script("arguments[0].click();", button)),
                    ("Force click with events", lambda: self.driver.execute_script("""
                        arguments[0].dispatchEvent(new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }));
                    """, button)),
                    ("ActionChains click", lambda: ActionChains(self.driver).move_to_element(button).click().perform()),
                    ("Focus and click", lambda: (self.driver.execute_script("arguments[0].focus();", button), button.click())[1])
                ]
                
                for i, (approach_name, approach) in enumerate(click_approaches):
                    try:
                        print(f"Trying {approach_name}...")
                        approach()
                        time.sleep(2)
                        
                        final_class = button.get_attribute('class')
                        print(f"Final button class: {final_class}")
                        
                        if 'selected' in final_class or 'active' in final_class:
                            print(f"SUCCESS: Button state changed using {approach_name}!")
                            print("Third party pickup selected successfully!")
                            print("AUTOMATION STOPPED - Manual continuation required")
                            time.sleep(300)
                            return True
                        else:
                            print(f"{approach_name} - no visual change detected")
                            
                    except Exception as e:
                        print(f"{approach_name} failed: {e}")
                        continue
                        
                print("Trying all buttons systematically...")
                for btn_index, btn in enumerate(buttons):
                    try:
                        print(f"Clicking button {btn_index + 1}...")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        
                        initial_class = btn.get_attribute('class')
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        final_class = btn.get_attribute('class')
                        
                        print(f"Button {btn_index + 1}: {initial_class} -> {final_class}")
                        
                        if 'selected' in final_class or 'active' in final_class:
                            print(f"SUCCESS: Button {btn_index + 1} was selected!")
                            print("AUTOMATION STOPPED - Manual continuation required")
                            time.sleep(300)
                            return True
                            
                    except Exception as e:
                        print(f"Button {btn_index + 1} click failed: {e}")
                        continue
                        
        except Exception as e:
            print(f"Direct approach failed: {e}")
        
        print("Alternative: looking for any clickable elements in the area...")
        try:
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                ".rc-segmented-control button, .rc-segmented-control-item button, button[role='radio']")
            
            for i, element in enumerate(clickable_elements):
                try:
                    print(f"Trying clickable element {i+1}...")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(2)
                    
                    if self.verify_third_party_selection():
                        print(f"SUCCESS: Element {i+1} worked!")
                        print("AUTOMATION STOPPED - Manual continuation required")
                        time.sleep(300)
                        return True
                        
                except Exception as e:
                    print(f"Element {i+1} failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"Alternative approach failed: {e}")
        
        print("Could not find or click third party pickup button")
        print("AUTOMATION STOPPED - Manual intervention required")
        time.sleep(300)
        return False

    def verify_third_party_selection(self):
        try:
            indicators = [
                "input[name*='pickupPersonFirstName']",
                "input[name*='pickupPersonLastName']", 
                "input[id*='thirdParty']",
                "input[id*='pickupPerson']",
                "//*[contains(text(), 'pickup person') or contains(text(), 'authorized person')]",
                ".rc-segmented-control-button[aria-pressed='true']",
                ".rc-segmented-control-button.selected",
                ".rc-segmented-control-button[data-selected='true']"
            ]
            
            for indicator in indicators:
                try:
                    if indicator.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, indicator)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    
                    if elements:
                        print(f"Found indicator of third party selection: {indicator}")
                        return True
                except:
                    continue
            
            page_source = self.driver.page_source.lower()
            third_party_keywords = ["pickup person", "authorized person", "someone else", "third party"]
            
            for keyword in third_party_keywords:
                if keyword in page_source:
                    print(f"Found third party keyword in page: {keyword}")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error verifying third party selection: {e}")
            return False

    def verify_third_party_selection(self):
        try:
            indicators = [
                "input[name*='pickupPersonFirstName']",
                "input[name*='pickupPersonLastName']", 
                "input[id*='thirdParty']",
                "input[id*='pickupPerson']",
                "//*[contains(text(), 'pickup person') or contains(text(), 'authorized person')]",
                ".rc-segmented-control-button[aria-pressed='true']",
                ".rc-segmented-control-button.selected",
                ".rc-segmented-control-button[data-selected='true']"
            ]
            
            for indicator in indicators:
                try:
                    if indicator.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, indicator)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    
                    if elements:
                        print(f"Found indicator of third party selection: {indicator}")
                        return True
                except:
                    continue
            
            page_source = self.driver.page_source.lower()
            third_party_keywords = ["pickup person", "authorized person", "someone else", "third party"]
            
            for keyword in third_party_keywords:
                if keyword in page_source:
                    print(f"Found third party keyword in page: {keyword}")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error verifying third party selection: {e}")
            return False

    def run_purchase_flow(self):
        if self._stopped:
            return False
        
        print(f"Starting purchase flow for iPhone {self.purchase_count + 1}...")
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
        time.sleep(2)
        
        if not self.click_applecare_no_coverage():
            print("❌ Failed to select no coverage")
            return False
        
        time.sleep(1)
        
        if not self.add_to_bag():
            print("❌ Failed to add to bag")
            return False
        
        time.sleep(2)
        return self.handle_bag_page()

    def run(self):
        try:
            print("🎯 Starting Apple automation...")
            print(f"📱 Target: {self.max_purchases} iPhones")
            print(f"👤 Contact: {self.user_data['first_name']} {self.user_data['last_name']}")
            print(f"📍 Zip Code: {self.user_data['zip_code']}")
            
            self.setup_driver()
            
            if self._stopped:
                return False
            
            print("🌐 Opening Apple website...")
            self.driver.get(self.config.PRODUCT_URL)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ Page loaded successfully")
            
            self.saved_link = self.driver.current_url
            print(f"💾 Saved page URL: {self.saved_link}")
            
            if not self.run_purchase_flow():
                print("❌ Purchase flow failed")
                return False
            
            print("🎉 SUCCESS: Automation completed up to third party pickup!")
            return True
            
        except Exception as e:
            print(f"💥 Error occurred: {e}")
            return False
        finally:
            print("ℹ️ Browser will remain open for manual continuation...")


if __name__ == "__main__":
    automation = AppleAutomation()
    automation.run()