import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains



class iPhone17PreorderTest:
    def __init__(self):
        self.driver = None
        self.product_url = "https://www.apple.com/shop/buy-iphone/iphone-17-pro/6.3-inch-display-256gb-cosmic-orange-unlocked"
        self.test_email = "ayoubech-chetyouy@hotmail.com"
        self.test_password = "LOVEyourself123."
        
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-automation")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def click_element_reliably(self, element, description="element"):
        """
        Try multiple methods to click an element reliably
        """
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
        selectors = [
            "[class*='applecare'][class*='no']",
            "[data-autom*='noapple']",
            "[data-autom*='no-applecare']",
            "button[aria-label*='No AppleCare']",
            "button[aria-label*='no coverage']",
            "input[value*='no']:not([type='hidden'])",
            "label[for*='no']:not([style*='display: none'])",
            "[class*='coverage'][class*='none']",
            "[data-value='none']",
            "[data-coverage='none']"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if self.click_element_reliably(element, f"'no coverage' button using selector: {selector}"):
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    if any(phrase in text for phrase in ["no applecare", "no coverage", "none", "skip"]):
                        if self.click_element_reliably(button, f"button with text: '{button.text}'"):
                            return True
            
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                if label.is_displayed():
                    text = label.text.lower()
                    if any(phrase in text for phrase in ["no applecare", "no coverage", "none"]):
                        if self.click_element_reliably(label, f"label with text: '{label.text}'"):
                            return True
        except Exception as e:
            print(f"Text-based search failed: {e}")
        
        print("Could not find 'no coverage' button")
        return False
    
    def click_proceed_button(self):
        selectors = [
            "button[name='proceed']",
            "button[value='proceed']",
            "input[type='submit'][name='proceed']",
            "input[type='submit'][value='proceed']",
            "[class*='if-progress-step-current'] button",
            "[aria-current='step'] button",
            "button[aria-label*='Browse iPhone accessories']"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if self.click_element_reliably(element, f"proceed button using selector: {selector}"):
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    button_html = button.get_attribute('outerHTML').lower()
                    if any(phrase in text or phrase in button_html for phrase in [
                        "proceed", "browse iphone accessories", "continue", "next"
                    ]):
                        if self.click_element_reliably(button, f"proceed button with text: '{button.text}'"):
                            return True
            
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_type = input_elem.get_attribute('type')
                    input_value = input_elem.get_attribute('value')
                    input_name = input_elem.get_attribute('name')
                    if input_type in ['submit', 'button'] and (input_value or input_name):
                        if input_value and "proceed" in input_value.lower():
                            if self.click_element_reliably(input_elem, f"input with value: '{input_value}'"):
                                return True
                        elif input_name and "proceed" in input_name.lower():
                            if self.click_element_reliably(input_elem, f"input with name: '{input_name}'"):
                                return True
        except Exception as e:
            print(f"Text-based search for proceed button failed: {e}")
        
        print("Could not find proceed button")
        return False

    def click_payment_method_button(self):
        selectors = [
            "[aria-label*='Choose a payment method and review details']",
            "[class*='ic-progress-step-current'] button",
            "[aria-current='step'] button",
            ".ic-progress-step-current button",
            "[class*='progress-step'][class*='current'] button",
            "button[aria-label*='payment method']",
            "button[aria-label*='review details']"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if self.click_element_reliably(element, f"payment method button using selector: {selector}"):
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    button_html = button.get_attribute('outerHTML').lower()
                    aria_label = button.get_attribute('aria-label') or ""
                    if any(phrase in text or phrase in button_html or phrase in aria_label.lower() for phrase in [
                        "choose a payment method", "payment method", "review details", 
                        "payment", "checkout", "continue to payment"
                    ]):
                        if self.click_element_reliably(button, f"payment method button with text: '{button.text}' or aria-label: '{aria_label}'"):
                            return True
        except Exception as e:
            print(f"Text-based search for payment method button failed: {e}")
        
        print("Could not find payment method button")
        return False

    def click_continue_button(self):
        selectors = [
            "button[name='proceed'][value='proceed']",
            "button[data-autom='proceed']",
            "[class*='button'][class*='button-block'][class*='button-super']",
            "button[type='submit'][name='proceed']",
            ".re-summaryheader-button button"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if self.click_element_reliably(element, f"continue button using selector: {selector}"):
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    button_html = button.get_attribute('outerHTML').lower()
                    if any(phrase in text or phrase in button_html for phrase in [
                        "continue", "proceed", "next", "go to checkout"
                    ]):
                        if self.click_element_reliably(button, f"continue button with text: '{button.text}'"):
                            return True
        except Exception as e:
            print(f"Text-based search for continue button failed: {e}")
        
        print("Could not find continue button")
        return False

    def click_add_to_cart(self):
        selectors = [
            "button[name='add-to-cart']",
            "button[value='add-to-cart']",
            "button[data-autom*='add-to-cart']",
            "button[data-analytics-title*='add-to-cart']",
            "button[data-analytics-title*='pre-order']",
            ".as-purchaseinfo-button",
            "[class*='add-to-cart']",
            "button[aria-label*='Add to Cart']",
            "button[aria-label*='Pre-order']",
            "input[type='submit'][name='add-to-cart']"
        ]
        
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if self.click_element_reliably(element, f"add to cart button using selector: {selector}"):
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    button_html = button.get_attribute('outerHTML').lower()
                    if any(phrase in text or phrase in button_html for phrase in [
                        "add to cart", "add to bag", "pre-order", "get ready for pre-order",
                        "buy now", "purchase", "add to basket"
                    ]):
                        if self.click_element_reliably(button, f"button with text: '{button.text}'"):
                            return True
            
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_type = input_elem.get_attribute('type')
                    input_value = input_elem.get_attribute('value')
                    if input_type in ['submit', 'button'] and input_value:
                        value_text = input_value.lower()
                        if any(phrase in value_text for phrase in [
                            "add to cart", "add to bag", "pre-order", "buy now", "purchase"
                        ]):
                            if self.click_element_reliably(input_elem, f"input with value: '{input_value}'"):
                                return True
        except Exception as e:
            print(f"Text-based search for add to cart failed: {e}")
        
        print("Could not find add to cart / pre-order button")
        return False

    def handle_login(self):
        try:
            print("Checking for login form...")
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            page_title = self.driver.title
            print(f"Page title: {page_title}")
            
            try:
                signin_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "signin-container"))
                )
                print("Found signin container")
            except (TimeoutException, NoSuchElementException):
                print("No signin container found")
                return True
            
            print("Waiting for JavaScript to load login form...")
            time.sleep(5)
            
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframe(s) on the page")
            
            success = self._find_login_form_in_context("main page")
            if success:
                return True
            
            for i, iframe in enumerate(iframes):
                if not iframe.is_displayed():
                    continue
                try:
                    print(f"Switching to iframe {i+1}...")
                    self.driver.switch_to.frame(iframe)
                    success = self._find_login_form_in_context(f"iframe {i+1}")
                    if success:
                        return True
                except Exception as e:
                    print(f"Error accessing iframe {i+1}: {e}")
                finally:
                    self.driver.switch_to.default_content()
            
            print("No login form detected in main page or iframes, proceeding...")
            return True
                
        except Exception as e:
            print(f"Login process failed: {e}")
            return False
            
    def _find_login_form_in_context(self, context_name):
        try:
            print(f"Searching for login form in {context_name}...")
            
            apple_id_selectors = [
                "input[id='account_name_text_field']",
                "input[placeholder*='Email or Phone Number']",
                "input[placeholder*='Apple ID']",
                "input[type='text'][autocomplete='username']",
                "input[name='accountName']",
                "input[id*='apple']",
                "input[class*='signin']",
                "input[type='text']",
                "input[type='email']"
            ]
            
            email_input = None
            for selector in apple_id_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"Found visible and enabled email input in {context_name}")
                            email_input = element
                            break
                except Exception as e:
                    continue
                if email_input:
                    break
            
            if email_input:
                print(f"Proceeding with login in {context_name}")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_input)
                time.sleep(1)
                
                email_input.clear()
                email_input.send_keys(self.test_email)
                print(f"Entered email: {self.test_email}")
                
                # Try Tab + Enter combination for better compatibility
                email_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                time.sleep(1)
                
                print("Waiting 10 seconds for continue button to appear...")
                time.sleep(10)
                
                print("Now looking for continue button...")
                
                # Get all buttons AFTER the wait
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                print(f"Found {len(all_buttons)} total buttons in {context_name}")
                for i, btn in enumerate(all_buttons):
                    try:
                        btn_text = btn.text or 'no text'
                        btn_class = btn.get_attribute('class') or 'no class'
                        btn_id = btn.get_attribute('id') or 'no id'
                        btn_aria = btn.get_attribute('aria-label') or 'no aria'
                        is_displayed = btn.is_displayed()
                        is_enabled = btn.is_enabled()
                        print(f"  Button {i+1}: text='{btn_text}', id='{btn_id}', aria='{btn_aria}', displayed={is_displayed}, enabled={is_enabled}")
                    except Exception as e:
                        print(f"  Button {i+1}: Error getting info - {e}")
                
                continue_button_selectors = [
                    "button[id='continue-password']",
                    "button[id='sign-in']",  # Added this based on your log
                    "button[class*='continue-password']",
                    "button[class*='tk-subbody']",
                    "button[style*='display:inline']",
                    "button[aria-label*='Continue']",
                    "button[data-testid*='continue']",
                    "button[type='submit']",
                    "input[type='submit']",
                    "button",
                ]
                
                continue_button_clicked = False
                for selector in continue_button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"Selector '{selector}': found {len(buttons)} buttons")
                        for j, button in enumerate(buttons):
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    button_text = button.text.lower()
                                    button_value = button.get_attribute('value') or ''
                                    button_aria = button.get_attribute('aria-label') or ''
                                    button_class = button.get_attribute('class') or ''
                                    button_id = button.get_attribute('id') or ''
                                    
                                    print(f"  Checking button {j+1}: text='{button_text}', aria='{button_aria}', class='{button_class}', id='{button_id}'")
                                    
                                    # Check for Continue with Password specifically or sign-in button
                                    if ('continue' in button_text and 'password' in button_text) or \
                                       ('continue' in button_aria.lower() and 'password' in button_aria.lower()) or \
                                       'continue-password' in button_class.lower() or \
                                       button_id == 'sign-in' or \
                                       'continue' in button_aria.lower():
                                        print(f"Found continue/sign-in button in {context_name}")
                                        if self.click_element_reliably(button, f"continue button (id: {button_id}, aria: {button_aria})"):
                                            continue_button_clicked = True
                                            break
                                    # Fallback for any continue/next/submit button
                                    elif any(keyword in button_text or keyword in button_value.lower() or keyword in button_aria.lower() 
                                           for keyword in ['continue', 'next', 'sign in', 'submit', 'proceed']):
                                        print(f"Found fallback continue button in {context_name}: '{button_text}' / '{button_aria}'")
                                        if self.click_element_reliably(button, f"fallback continue button"):
                                            continue_button_clicked = True
                                            break
                            except Exception as e:
                                print(f"  Error checking button {j+1}: {e}")
                                continue
                        if continue_button_clicked:
                            break
                    except Exception as e:
                        print(f"Error with selector '{selector}': {e}")
                        continue
                
                if continue_button_clicked:
                    print("Continue button clicked, waiting for password field...")
                    time.sleep(5)
                else:
                    print("No continue button found, proceeding to look for password field...")
                    time.sleep(2)
                
                password_selectors = [
                    "input[id='password_text_field']",
                    "input[type='password']",
                    "input[placeholder*='Password']",
                    "input[autocomplete='current-password']",
                    "input[name='password']"
                ]
                
                password_input = None
                for attempt in range(3):
                    for selector in password_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                try:
                                    if element.is_displayed() and element.is_enabled():
                                        print(f"Found visible password input in {context_name}")
                                        password_input = element
                                        break
                                except Exception as e:
                                    continue
                        except Exception as e:
                            continue
                        if password_input:
                            break
                    if password_input:
                        break
                    time.sleep(2)
                
                if password_input:
                    print(f"Filling password in {context_name}")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", password_input)
                    time.sleep(1)
                    
                    password_input.clear()
                    password_input.send_keys(self.test_password)
                    print(f"Entered password: {self.test_password}")
                    
                    # Use multiple methods to submit password
                    try:
                        password_input.send_keys(Keys.RETURN)
                        print("Pressed Enter on password field")
                    except:
                        try:
                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                            print("Used ActionChains to press Enter")
                        except:
                            print("Could not submit password with keyboard")
                    
                    time.sleep(3)
                    
                    print(f"Login process completed in {context_name}")
                    return True
                else:
                    print(f"Password field not found in {context_name}")
                    return False
            else:
                print(f"No email input found in {context_name}")
                return False
                
        except Exception as e:
            print(f"Error searching in {context_name}: {e}")
            return False
    
    def run_test(self):
        try:
            print("Starting iPhone 17 Pro pre-order test...")
            self.setup_driver()
            print(f"Opening: {self.product_url}")
            self.driver.get(self.product_url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Page loaded successfully")
            
            print("Scrolling down to load content...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.22);")
            time.sleep(3)
            
            if self.wait_and_click_no_coverage():
                print("Successfully clicked 'no coverage' option!")
                time.sleep(2)
                
                if self.click_add_to_cart():
                    print("Successfully clicked add to cart / pre-order button!")
                    time.sleep(3)
                    
                    if self.click_proceed_button():
                        print("Successfully clicked proceed button!")
                        time.sleep(3)
                        
                        if self.click_continue_button():
                            print("Successfully clicked continue button!")
                            time.sleep(3)
                            
                            if self.click_payment_method_button():
                                print("Successfully clicked payment method button!")
                                
                                print("Now handling login process...")
                                if self.handle_login():
                                    print("Login completed successfully!")
                                else:
                                    print("Login failed or not required")
                            else:
                                print("Failed to find or click payment method button")
                        else:
                            print("Failed to find or click continue button")
                    else:
                        print("Failed to find or click proceed button")
                else:
                    print("Failed to find or click add to cart button")
            else:
                print("Failed to find or click 'no coverage' option")
                if self.click_add_to_cart():
                    print("Successfully clicked add to cart / pre-order button!")
                    time.sleep(3)
                    
                    if self.click_proceed_button():
                        print("Successfully clicked proceed button!")
                        time.sleep(3)
                        
                        if self.click_continue_button():
                            print("Successfully clicked continue button!")
                            time.sleep(3)
                            
                            if self.click_payment_method_button():
                                print("Successfully clicked payment method button!")
                                
                                print("Now handling login process...")
                                if self.handle_login():
                                    print("Login completed successfully!")
                                else:
                                    print("Login failed or not required")
                            else:
                                print("Failed to find or click payment method button")
                        else:
                            print("Failed to find or click continue button")
                    else:
                        print("Failed to find or click proceed button")
                else:
                    print("Failed to find or click add to cart button")
            
            print("Waiting 60 seconds to observe results...")
            time.sleep(60)
            
            print("Test completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return False
            
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()


def main():
    test = iPhone17PreorderTest()
    test.run_test()


if __name__ == "__main__":
    main()