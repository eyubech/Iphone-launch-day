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
        self.url_stuck_count = 0
        self.max_url_stuck = 3
        self.last_url = ''
        
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
        """Get unique email for this process"""
        if not self.process_email:
            try:
                self.process_email = self.email_manager.get_next_email(self.process_num)
                print(f"Process {self.process_num}: Assigned email: {self.process_email}")
            except Exception as e:
                print(f"Process {self.process_num}: Error getting email: {e}")
                # Fallback to default email
                self.process_email = self.user_data.get('email', 'default@example.com')
        
        return self.process_email

    def mark_email_status(self, success=True):
        """Mark email status based on automation result"""
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

    # Modify the _combine_automation_data method:
    def _combine_automation_data(self, card_data, person_data, settings_data):
        user_info = card_data.get('user_info', {})
        billing_info = card_data.get('billing_info', {})
        
        # Get unique email for this process
        process_email = self.get_process_email()
        
        return {
            'zip_code': settings_data['zip_code'],
            'street_address': settings_data['street_address'],
            'postal_code': settings_data['postal_code'],
            'first_name': user_info.get('first_name', person_data['first_name']),
            'last_name': user_info.get('last_name', person_data['last_name']),
            'email': process_email,  # Use unique process email
            'phone': user_info.get('phone', person_data['phone']),
            'credit_card': card_data['card_number'],
            'expiry_date': card_data['expiry_date'],
            'cvc': card_data['cvc'],
            'billing_first_name': billing_info.get('first_name', user_info.get('first_name', person_data['first_name'])),
            'billing_last_name': billing_info.get('last_name', user_info.get('last_name', person_data['last_name'])),
            'billing_street_address': billing_info.get('street_address', settings_data['street_address']),
            'billing_postal_code': billing_info.get('postal_code', settings_data['postal_code'])
        }
        
    def check_url_progress(self, step_name):
        current_url = self.driver.current_url
        
        if current_url == self.last_url:
            self.url_stuck_count += 1
            print(f"URL hasn't changed for {step_name}. Stuck count: {self.url_stuck_count}/{self.max_url_stuck}")
            
            if self.url_stuck_count >= self.max_url_stuck:
                print(f"Process appears stuck at {step_name} - URL not progressing")
                raise Exception(f"URL stuck at {step_name} - no progress detected")
        else:
            self.url_stuck_count = 0
            self.last_url = current_url
            print(f"URL changed successfully: {current_url}")
    
    def check_page_failure_indicators(self):
        try:
            page_source = self.driver.page_source.lower()
            title = self.driver.title.lower()
            
            failure_keywords = [
                'error', 'failed', 'unavailable', 'not found', 'timeout',
                'something went wrong', 'try again', 'service unavailable',
                'temporarily unavailable', 'access denied', 'forbidden',
                'internal server error', 'bad gateway', 'connection timed out'
            ]
            
            for keyword in failure_keywords:
                if keyword in page_source or keyword in title:
                    print(f"Failure indicator detected: '{keyword}' found in page")
                    raise Exception(f"Page failure detected: {keyword}")
            
            apple_errors = [
                'we\'re sorry', 'please try again', 'temporarily down',
                'high traffic', 'maintenance', 'system busy'
            ]
            
            for error in apple_errors:
                if error in page_source or error in title:
                    print(f"Apple-specific error detected: '{error}'")
                    raise Exception(f"Apple site error: {error}")
                    
        except Exception as e:
            if "Page failure detected" in str(e) or "Apple site error" in str(e):
                raise e
            else:
                print(f"Error checking page indicators: {e}")
    
    def monitor_progress(self, step_name, timeout=30):
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                self.check_page_failure_indicators()
                self.check_url_progress(step_name)
                return True
            except Exception as e:
                if "stuck" in str(e) or "failure detected" in str(e) or "error" in str(e):
                    raise e
                time.sleep(2)
        
        raise Exception(f"Timeout waiting for {step_name} to complete")
            
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
        
    def test_proxy_connection(self):
        if self.use_proxy:
            success, ip_info = self.proxy.test_proxy(self.process_num)
            if success:
                print(f"Process {self.process_num}: Proxy test successful - IP: {ip_info}")
                return True
            else:
                print(f"Process {self.process_num}: Proxy test failed - {ip_info}")
                return False
        return True
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        
        for option in self.config.BROWSER_OPTIONS:
            options.add_argument(option)
            
        if self.use_proxy:
            proxy_options = self.proxy.get_chrome_proxy_options(self.process_num)
            for proxy_option in proxy_options:
                options.add_argument(proxy_option)
            print(f"Process {self.process_num}: Chrome configured with proxy")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if self.use_proxy:
                print(f"Process {self.process_num}: Testing proxy connection...")
                if not self.test_proxy_connection():
                    print(f"Process {self.process_num}: Warning - Proxy connection test failed, continuing anyway")
            
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

    def handle_critical_error(self, error_msg, step_name):
        self.error_count += 1
        print(f"CRITICAL ERROR in {step_name}: {error_msg}")
        print(f"Error count: {self.error_count}/{self.max_errors}")
        
        if self.error_count >= self.max_errors:
            print("Maximum error threshold reached. Restarting automation...")
            self.restart_automation()
            return False
        
        print("Attempting to continue with error recovery...")
        time.sleep(5)
        return True
    
    def restart_automation(self):
        try:
            print("Restarting automation process...")
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        self.driver = None
        self.error_count = 0
        self.purchase_count = 0
        self.url_stuck_count = 0
        self.last_url = ''
        time.sleep(3)
        
        return self.run()
    
    def safe_execute(self, func, func_name, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WebDriverException as e:
            self.handle_critical_error(f"WebDriver error: {str(e)}", func_name)
            return False
        except TimeoutException as e:
            self.handle_critical_error(f"Timeout error: {str(e)}", func_name)
            return False
        except Exception as e:
            self.handle_critical_error(f"Unexpected error: {str(e)}", func_name)
            return False

    def click_element(self, selector, element_name, timeout=10):
        if self._stopped:
            return False
        
        def _click_attempt():
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"✓ {element_name} clicked successfully")
            
            time.sleep(3)
            self.monitor_progress(f"after_{element_name.replace(' ', '_')}_click", timeout=15)
            
            return True
        
        result = self.safe_execute(_click_attempt, f"click_element_{element_name}")
        if result is False:
            print(f"Failed to click {element_name} - triggering restart")
            return False
        return result

    def click_applecare_no_coverage(self):
        if self._stopped:
            return False
        
        def _click_no_coverage():
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
                    
            raise Exception("Could not find AppleCare no coverage option after all methods")
        
        result = self.safe_execute(_click_no_coverage, "click_applecare_no_coverage")
        return result if result is not False else False
    
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
        
        def _add_to_bag_attempt():
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
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Add to bag clicked successfully")
                    
                    time.sleep(5)
                    self.monitor_progress("add_to_bag", timeout=20)
                    
                    return True
                except:
                    continue
            
            raise Exception("Could not find add to bag button with any selector")
        
        result = self.safe_execute(_add_to_bag_attempt, "add_to_bag")
        return result if result is not False else False

    def handle_bag_page(self):
        if self._stopped:
            return False
            
        print("Waiting for bag page to load...")
        time.sleep(3)
        
        self.purchase_count += 1
        print(f"iPhone {self.purchase_count} added to bag")
        
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
        
        def _proceed_attempt():
            print("Looking for checkout button...")
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
                    time.sleep(0.5)
                    element.click()
                    print("Proceed to checkout clicked successfully")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            raise Exception("Could not find proceed to checkout button")
        
        result = self.safe_execute(_proceed_attempt, "proceed_to_checkout")
        if result:
            return self.handle_checkout_flow()
        return False

    def handle_checkout_flow(self):
        if self._stopped:
            return False
        
        def _checkout_attempt():
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
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Checkout button clicked successfully")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            raise Exception("Could not find checkout button")
        
        result = self.safe_execute(_checkout_attempt, "handle_checkout_flow")
        if result:
            return self.handle_guest_login()
        return False

    def handle_guest_login(self):
        if self._stopped:
            return False
        
        def _guest_login_attempt():
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
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print("Guest login clicked successfully")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            raise Exception("Could not find guest login button")
        
        result = self.safe_execute(_guest_login_attempt, "handle_guest_login")
        if result:
            return self.continue_after_guest_login()
        return False

    def continue_after_guest_login(self):
        if self._stopped:
            return False
        
        def _third_party_attempt():
            print("Continuing after guest login - enhanced from direct-order.py...")
            time.sleep(8)
            
            self.monitor_progress("guest_login_completion", timeout=20)
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".rc-segmented-control-button"))
            )
            print("Segmented control buttons are now present")
            
            print("Direct approach: clicking second rc-segmented-control-button...")
            buttons = self.driver.find_elements(By.CSS_SELECTOR, ".rc-segmented-control-button")
            print(f"Found {len(buttons)} rc-segmented-control-button elements")
            
            if len(buttons) < 2:
                raise Exception("Expected at least 2 buttons, found only " + str(len(buttons)))
            
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
                        
                        try:
                            self.monitor_progress("third_party_selection", timeout=15)
                            print("AUTOMATION CYCLE COMPLETED - Ready for next cycle")
                            time.sleep(5)
                        except:
                            print("Progress monitoring completed - cycle finished")
                            time.sleep(5)
                        
                        return True
                    else:
                        print(f"{approach_name} - no visual change detected")
                        
                except Exception as e:
                    print(f"{approach_name} failed: {e}")
                    continue
            
            self.check_page_failure_indicators()
            raise Exception("All click approaches failed for third party pickup")
        
        result = self.safe_execute(_third_party_attempt, "continue_after_guest_login")
        return result if result is not False else False

    def run_purchase_flow(self):
        if self._stopped:
            return False
        
        print(f"Starting purchase flow for iPhone {self.purchase_count + 1}...")
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
        time.sleep(2)
        
        if not self.click_applecare_no_coverage():
            print("Failed to select no coverage")
            return False
        
        time.sleep(1)
        
        if not self.add_to_bag():
            print("Failed to add to bag")
            return False
        
        time.sleep(2)
        return self.handle_bag_page()

    def run(self):
        automation_success = False
        
        try:
            proxy_status = "WITH PROXY" if self.use_proxy else "WITHOUT PROXY"
            print(f"Process {self.process_num}: Starting Apple automation {proxy_status}...")
            print(f"Product URL: {self.config.PRODUCT_URL}")
            print(f"Target: {self.max_purchases} iPhones")
            
            # Get unique email for this process FIRST
            try:
                process_email = self.get_process_email()
                print(f"Process {self.process_num}: Using email: {process_email}")
            except Exception as e:
                print(f"Process {self.process_num}: Email assignment error: {e}")
                print(f"Process {self.process_num}: Continuing with fallback email")
            
            print(f"Contact: {self.user_data['first_name']} {self.user_data['last_name']}")
            print(f"Email: {self.user_data['email']}")
            print(f"Zip Code: {self.user_data['zip_code']}")
            
            def _main_run():
                """Internal run function with error handling"""
                nonlocal automation_success
                
                # Reset counters for this run
                self.purchase_count = 0
                self.error_count = 0
                self.url_stuck_count = 0
                self.last_url = ''
                
                # Setup WebDriver
                if not self.setup_driver():
                    raise Exception("Failed to setup WebDriver")
                
                if self._stopped:
                    print(f"Process {self.process_num}: Stopped before starting")
                    return False
                
                # Navigate to product page
                print(f"Process {self.process_num}: Opening Apple website...")
                self.driver.get(self.config.PRODUCT_URL)
                
                # Wait for page to load
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print(f"Process {self.process_num}: Page loaded successfully")
                
                # Save the current URL for potential restarts
                self.saved_link = self.driver.current_url
                print(f"Process {self.process_num}: Saved page URL: {self.saved_link}")
                
                # Check for any immediate page errors
                self.check_page_failure_indicators()
                
                # Start the purchase flow
                success = self.run_purchase_flow()
                
                if success:
                    print(f"Process {self.process_num}: SUCCESS - Automation cycle completed!")
                    automation_success = True
                    return True
                else:
                    print(f"Process {self.process_num}: Purchase flow failed")
                    return False
            
            # Execute the main automation flow with error handling
            result = self.safe_execute(_main_run, "main_run")
            
            # Determine final success status
            final_success = result and automation_success
            
            # Mark email status based on result
            try:
                self.mark_email_status(success=final_success)
            except Exception as e:
                print(f"Process {self.process_num}: Error updating email status: {e}")
            
            # Cleanup WebDriver
            if self.driver:
                try:
                    print(f"Process {self.process_num}: Closing browser...")
                    self.driver.quit()
                except Exception as e:
                    print(f"Process {self.process_num}: Error closing browser: {e}")
                finally:
                    self.driver = None
            
            # Final status report
            if final_success:
                print(f"Process {self.process_num}: COMPLETED SUCCESSFULLY")
                print(f"Process {self.process_num}: Email {self.process_email} marked as completed")
            else:
                print(f"Process {self.process_num}: FAILED - Email marked for retry")
            
            return final_success
            
        except KeyboardInterrupt:
            print(f"Process {self.process_num}: Automation interrupted by user")
            try:
                self.mark_email_status(success=False)
            except:
                pass
            self.stop()
            return False
            
        except Exception as e:
            print(f"Process {self.process_num}: Unexpected error in main run: {e}")
            traceback.print_exc()
            
            # Mark email as failed for retry
            try:
                self.mark_email_status(success=False)
            except:
                pass
            
            # Ensure cleanup
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                finally:
                    self.driver = None
            
            return False
        
        finally:
            # Final cleanup - ensure driver is closed
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            # Log final process status
            status_text = "SUCCESS" if automation_success else "FAILED"
            print(f"Process {self.process_num}: Final status - {status_text}")


if __name__ == "__main__":
    automation = AppleAutomation()
    automation.run()