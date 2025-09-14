import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class iPhoneOrderBot:
    def __init__(self):
        self.driver = None
        self.product_url = "http://localhost:8080/apple-test"
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-automation")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
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
        
        # First try the exact ID from your screenshot
        try:
            print("Trying exact ID: applecare-selector-no-applecare-option")
            element = self.driver.find_element(By.ID, "applecare-selector-no-applecare-option")
            if element.is_displayed():
                print("Found element with exact ID, trying multiple click methods...")
                if self.click_and_verify_selection(element, "no applecare radio input"):
                    return True
        except Exception as e:
            print(f"Exact ID failed: {e}")
        
        # Try the label for that radio
        try:
            print("Trying label for no applecare option")
            label = self.driver.find_element(By.CSS_SELECTOR, "label[for='applecare-selector-no-applecare-option']")
            if label.is_displayed():
                print("Found label, trying click...")
                if self.click_and_verify_selection(label, "no applecare label"):
                    return True
        except Exception as e:
            print(f"Label click failed: {e}")
        
        # Find all radio inputs and try them
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
        """Click element and verify it was actually selected"""
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
                
                # Get initial state
                initial_checked = element.get_attribute('checked')
                print(f"Initial checked state: {initial_checked}")
                
                method()
                time.sleep(1)
                
                # Check if it's now selected
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
    
    def run_test(self):
        try:
            print("Starting iPhone order test...")
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
            else:
                print("Failed to find or click 'no coverage' option")
            
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
    test = iPhoneOrderBot()
    test.run_test()

if __name__ == "__main__":
    main()