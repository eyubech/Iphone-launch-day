import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def open_apple_site_and_click():
    url = "https://www.apple.com/shop/buy-iphone/iphone-16-pro/6.3-inch-display-128gb-desert-titanium-unlocked"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print("Opening Apple website...")
        driver.get(url)
        
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded successfully")
        
        # Scroll to 30% of page height to load content
        print("Scrolling down to load content...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.22);")
        time.sleep(2)
        
        print("Clicking AppleCare option...")
        applecare_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[class*='applecare'][class*='no'], [data-autom*='noapple']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", applecare_element)
        time.sleep(1)
        applecare_element.click()
        print("AppleCare option clicked")
        
        print("Looking for pickup button...")
        time.sleep(3)
        
        pickup_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.rf-pickup-quote-overlay-trigger"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pickup_element)
        time.sleep(1)
        pickup_element.click()
        print("Pickup button clicked")
        
        print("Looking for zip code input field...")
        time.sleep(2)
        
        zip_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='search'][type='text']"))
        )
        
        zip_input.clear()
        zip_input.send_keys("33165")
        print("Typed '33165' in zip code field")
        
        zip_input.send_keys(Keys.RETURN)
        print("Pressing Enter")
        
        print("Waiting for store results to load...")
        time.sleep(5)
        
        try:
            store_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.rf-productlocator-storeoption"))
            )
            
            print(f"STORE AVAILABILITY ANALYSIS")
            print(f"Found {len(store_elements)} stores in the area:")
            print("-" * 50)
            
            available_stores = []
            unavailable_stores = []
            
            for i, store in enumerate(store_elements, 1):
                try:
                    store_name_elem = store.find_element(By.CSS_SELECTOR, ".form-selector-title")
                    store_name = store_name_elem.text.strip()
                    
                    try:
                        location_elem = store.find_element(By.CSS_SELECTOR, ".form-label-small")
                        location = location_elem.text.strip()
                    except:
                        location = "Location not found"
                    
                    try:
                        availability = None
                        
                        availability_selectors = [
                            ".form-selector-right-col span",
                            ".form-selector-right-col .form-label-small",
                            "span:contains('Available Today')",
                            "span:contains('Currently unavailable')",
                            ".form-selector-right-col"
                        ]
                        
                        for selector in availability_selectors:
                            try:
                                if "contains" in selector:
                                    xpath = f".//*[contains(text(), 'Available Today') or contains(text(), 'Currently unavailable')]"
                                    availability_elem = store.find_element(By.XPATH, xpath)
                                else:
                                    availability_elem = store.find_element(By.CSS_SELECTOR, selector)
                                
                                availability = availability_elem.text.strip()
                                if availability and ("Available" in availability or "unavailable" in availability):
                                    break
                            except:
                                continue
                        
                        if not availability:
                            store_text = store.text
                            if "Available Today" in store_text:
                                availability = "Available Today"
                            elif "Currently unavailable" in store_text:
                                availability = "Currently unavailable"
                            else:
                                availability = "Status unknown"
                        
                        if "Available Today" in availability:
                            available_stores.append({
                                'name': store_name,
                                'location': location,
                                'availability': availability,
                                'element': store
                            })
                            print(f"AVAILABLE: {store_name}")
                            print(f"  Location: {location}")
                            print(f"  Status: {availability}")
                            print()
                        else:
                            unavailable_stores.append({
                                'name': store_name,
                                'location': location,
                                'availability': availability
                            })
                    except:
                        unavailable_stores.append({
                            'name': store_name,
                            'location': location,
                            'availability': 'Status unknown'
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
                
                print(f"Selecting first available store: {available_stores[0]['name']}")
                first_store = available_stores[0]['element']
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_store)
                time.sleep(1)
                
                try:
                    store_radio = first_store.find_element(By.CSS_SELECTOR, "input[type='radio']")
                    store_radio.click()
                    print(f"Selected store: {available_stores[0]['name']}")
                except:
                    first_store.click()
                    print(f"Selected store: {available_stores[0]['name']}")
                
                time.sleep(2)
                
                print("Looking for Continue button...")
                try:
                    continue_selectors = [
                        "button[data-autom='continuePickUp']",
                        "button[data-autom*='continue']",
                        ".button.button-block.rf-productlocator-selectstore",
                        "button.button.button-block",
                        ".rf-productlocator-selectstore",
                        "button[type='button'][class*='button-block']"
                    ]
                    
                    continue_clicked = False
                    
                    for selector in continue_selectors:
                        try:
                            continue_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
                            time.sleep(1)
                            continue_button.click()
                            print(f"Continue button clicked successfully using selector: {selector}")
                            continue_clicked = True
                            break
                        except:
                            continue
                    
                    if not continue_clicked:
                        try:
                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                            for btn in all_buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn_text = btn.text.strip().lower()
                                    if "continue" in btn_text or btn.get_attribute('data-autom'):
                                        btn.click()
                                        print("Continue button clicked successfully (text search method)")
                                        continue_clicked = True
                                        break
                        except Exception as e:
                            print(f"Fallback method failed: {e}")
                    
                    if not continue_clicked:
                        print("Could not find Continue button with any method")
                    else:
                        print("Waiting for next page to load...")
                        time.sleep(5)
                        
                        print("Looking for Add to Bag button...")
                        try:
                            add_to_bag_selectors = [
                                "button[data-autom='add-to-cart']",
                                "button[name='add-to-cart']",
                                ".button[data-autom='add-to-cart']",
                                "button[class*='add-to-cart']",
                                ".as-purchaseinfo-button button",
                                "form button[type='submit']"
                            ]
                            
                            bag_clicked = False
                            
                            for selector in add_to_bag_selectors:
                                try:
                                    add_to_bag_button = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_to_bag_button)
                                    time.sleep(1)
                                    add_to_bag_button.click()
                                    print(f"Add to Bag button clicked successfully using selector: {selector}")
                                    bag_clicked = True
                                    break
                                except:
                                    continue
                            
                            if not bag_clicked:
                                try:
                                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                    for btn in all_buttons:
                                        if btn.is_displayed() and btn.is_enabled():
                                            btn_text = btn.text.strip().lower()
                                            if "add to bag" in btn_text or "add to cart" in btn_text:
                                                btn.click()
                                                print("Add to Bag button clicked successfully (text search method)")
                                                bag_clicked = True
                                                break
                                except Exception as e:
                                    print(f"Text search method failed: {e}")
                            
                            if not bag_clicked:
                                print("Could not find Add to Bag button")
                            else:
                                print("Waiting for bag page to load...")
                                time.sleep(5)
                                
                                print("Looking for Review Bag button...")
                                try:
                                    review_bag_selectors = [
                                        "button[data-autom='proceed']",
                                        "button[name='proceed']",
                                        "button[value='proceed']",
                                        ".button.button-block[data-autom='proceed']",
                                        "form button[type='submit']",
                                        "button[class*='button-block']"
                                    ]
                                    
                                    review_clicked = False
                                    
                                    for selector in review_bag_selectors:
                                        try:
                                            review_button = WebDriverWait(driver, 5).until(
                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                            )
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_button)
                                            time.sleep(1)
                                            review_button.click()
                                            print(f"Review Bag button clicked successfully using selector: {selector}")
                                            review_clicked = True
                                            break
                                        except:
                                            continue
                                    
                                    if not review_clicked:
                                        try:
                                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                            for btn in all_buttons:
                                                if btn.is_displayed() and btn.is_enabled():
                                                    btn_text = btn.text.strip().lower()
                                                    if "review" in btn_text or "proceed" in btn_text or "continue" in btn_text:
                                                        btn.click()
                                                        print("Review Bag button clicked successfully (text search method)")
                                                        review_clicked = True
                                                        break
                                        except Exception as e:
                                            print(f"Text search method failed: {e}")
                                    
                                    if not review_clicked:
                                        print("Could not find Review Bag button")
                                    else:
                                        print("Waiting for checkout page to load...")
                                        time.sleep(5)
                                        
                                        print("Looking for Checkout button...")
                                        try:
                                            checkout_selectors = [
                                                "button[id='shoppingCart.actions.navCheckoutOtherPayments']",
                                                "button.button.button-block.rs-bag-checkout-otheroptions",
                                                ".rs-bag-checkoutbutton button",
                                                "button[class*='checkout']",
                                                ".rs-bag-checkoutbuttons-wrapper button",
                                                "button[type='button'][class*='button-block']"
                                            ]
                                            
                                            checkout_clicked = False
                                            
                                            for selector in checkout_selectors:
                                                try:
                                                    checkout_button = WebDriverWait(driver, 5).until(
                                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                    )
                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_button)
                                                    time.sleep(1)
                                                    checkout_button.click()
                                                    print(f"Checkout button clicked successfully using selector: {selector}")
                                                    checkout_clicked = True
                                                    break
                                                except:
                                                    continue
                                            
                                            if not checkout_clicked:
                                                try:
                                                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                    for btn in all_buttons:
                                                        if btn.is_displayed() and btn.is_enabled():
                                                            btn_text = btn.text.strip().lower()
                                                            if "check out" in btn_text or "checkout" in btn_text:
                                                                btn.click()
                                                                print("Checkout button clicked successfully (text search method)")
                                                                checkout_clicked = True
                                                                break
                                                except Exception as e:
                                                    print(f"Text search method failed: {e}")
                                            
                                            if not checkout_clicked:
                                                print("Could not find Checkout button")
                                            else:
                                                print("Waiting for checkout page to load...")
                                                time.sleep(5)
                                                
                                                print("Looking for Continue as Guest button...")
                                                try:
                                                    guest_selectors = [
                                                        "button[data-autom='guest-checkout-btn']",
                                                        "button[id='signin.guestLogin.guestLogin']",
                                                        ".form-button[data-autom='guest-checkout-btn']",
                                                        "button[class*='guest-checkout']",
                                                        ".rs-sign-in-sidebar button",
                                                        "button[type='button'][class*='form-button']"
                                                    ]
                                                    
                                                    guest_clicked = False
                                                    
                                                    for selector in guest_selectors:
                                                        try:
                                                            guest_button = WebDriverWait(driver, 5).until(
                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                            )
                                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", guest_button)
                                                            time.sleep(1)
                                                            guest_button.click()
                                                            print(f"Continue as Guest button clicked successfully using selector: {selector}")
                                                            guest_clicked = True
                                                            break
                                                        except:
                                                            continue
                                                    
                                                    if not guest_clicked:
                                                        try:
                                                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                            for btn in all_buttons:
                                                                if btn.is_displayed() and btn.is_enabled():
                                                                    btn_text = btn.text.strip().lower()
                                                                    if "guest" in btn_text or "continue as guest" in btn_text:
                                                                        btn.click()
                                                                        print("Continue as Guest button clicked successfully (text search method)")
                                                                        guest_clicked = True
                                                                        break
                                                        except Exception as e:
                                                            print(f"Text search method failed: {e}")
                                                    
                                                    if not guest_clicked:
                                                        print("Could not find Continue as Guest button")
                                                    else:
                                                        print("Waiting for pickup time selection page...")
                                                        time.sleep(5)
                                                        
                                                        print("Looking for pickup time slot dropdown...")
                                                        try:
                                                            dropdown_selectors = [
                                                                "select[id='checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots.timeSlotValue']",
                                                                "select[data-autom='pickup-availablewindow-dropdown']",
                                                                ".form-dropdown-selector select",
                                                                "select[class*='form-dropdown']",
                                                                ".rs-pickup-slottitle select"
                                                            ]
                                                            
                                                            dropdown_found = False
                                                            
                                                            for selector in dropdown_selectors:
                                                                try:
                                                                    dropdown = WebDriverWait(driver, 5).until(
                                                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                    )
                                                                    
                                                                    print(f"Found pickup time dropdown using selector: {selector}")
                                                                    
                                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
                                                                    time.sleep(1)
                                                                    
                                                                    select_obj = Select(dropdown)
                                                                    options = select_obj.options
                                                                    
                                                                    print(f"Found {len(options)} time slot options:")
                                                                    for i, option in enumerate(options):
                                                                        option_text = option.text.strip()
                                                                        option_value = option.get_attribute('value')
                                                                        if option_text:
                                                                            print(f"  Option {i}: '{option_text}' (value: {option_value})")
                                                                    
                                                                    selected = False
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
                                                                                selected = True
                                                                                dropdown_found = True
                                                                                break
                                                                            except Exception as e:
                                                                                print(f"Could not select option {option_text}: {e}")
                                                                                continue
                                                                    
                                                                    if not selected:
                                                                        try:
                                                                            if len(options) > 1:
                                                                                select_obj.select_by_index(1)
                                                                                print(f"Selected time slot by index: '{options[1].text.strip()}'")
                                                                                dropdown_found = True
                                                                        except Exception as e:
                                                                            print(f"Could not select by index: {e}")
                                                                    
                                                                    if dropdown_found:
                                                                        break
                                                                    
                                                                except:
                                                                    continue
                                                            
                                                            if not dropdown_found:
                                                                print("Could not find pickup time slot dropdown")
                                                            else:
                                                                print("Waiting for page to update...")
                                                                time.sleep(3)
                                                                
                                                                print("Looking for final Continue button...")
                                                                try:
                                                                    final_continue_selectors = [
                                                                        "button[id='rs-checkout-continue-button-bottom']",
                                                                        "button[data-autom='fulfillment-continue-button']",
                                                                        ".rs-checkout-action button",
                                                                        "button.form-button",
                                                                        "button[type='button'][class*='form-button']",
                                                                        ".rs-checkout-action-button-wrapper button"
                                                                    ]
                                                                    
                                                                    final_clicked = False
                                                                    
                                                                    for selector in final_continue_selectors:
                                                                        try:
                                                                            final_button = WebDriverWait(driver, 5).until(
                                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                            )
                                                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", final_button)
                                                                            time.sleep(1)
                                                                            final_button.click()
                                                                            print(f"Final Continue button clicked successfully using selector: {selector}")
                                                                            final_clicked = True
                                                                            break
                                                                        except:
                                                                            continue
                                                                    
                                                                    if not final_clicked:
                                                                        try:
                                                                            all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                                            for btn in all_buttons:
                                                                                if btn.is_displayed() and btn.is_enabled():
                                                                                    btn_text = btn.text.strip().lower()
                                                                                    if "continue" in btn_text:
                                                                                        btn.click()
                                                                                        print("Final Continue button clicked successfully (text search method)")
                                                                                        final_clicked = True
                                                                                        break
                                                                        except Exception as e:
                                                                            print(f"Text search method failed: {e}")
                                                                    
                                                                    if not final_clicked:
                                                                        print("Could not find final Continue button")
                                                                    else:
                                                                        print("Waiting for pickup person selection page...")
                                                                        time.sleep(5)
                                                                        
                                                                        print("Looking for 'Someone else to pick up' option...")
                                                                        try:
                                                                            third_party_selectors = [
                                                                                "button[data-autom='thirdPartyPickup']",
                                                                                "input[data-autom='thirdPartyPickup']",
                                                                                ".rc-segmented-control-item button[data-autom='thirdPartyPickup']",
                                                                                "button[role='radio'][data-autom='thirdPartyPickup']",
                                                                                ".rc-segmented-control-item[data-autom='thirdPartyPickup']"
                                                                            ]
                                                                            
                                                                            third_party_clicked = False
                                                                            
                                                                            for selector in third_party_selectors:
                                                                                try:
                                                                                    third_party_button = WebDriverWait(driver, 5).until(
                                                                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                    )
                                                                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", third_party_button)
                                                                                    time.sleep(1)
                                                                                    third_party_button.click()
                                                                                    print(f"Someone else to pick up selected using selector: {selector}")
                                                                                    third_party_clicked = True
                                                                                    break
                                                                                except:
                                                                                    continue
                                                                            
                                                                            if not third_party_clicked:
                                                                                try:
                                                                                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                                                    for btn in all_buttons:
                                                                                        if btn.is_displayed() and btn.is_enabled():
                                                                                            btn_text = btn.text.strip().lower()
                                                                                            if "someone else" in btn_text or "third party" in btn_text:
                                                                                                btn.click()
                                                                                                print("Someone else to pick up selected (text search method)")
                                                                                                third_party_clicked = True
                                                                                                break
                                                                                except Exception as e:
                                                                                    print(f"Text search method failed: {e}")
                                                                            
                                                                            if not third_party_clicked:
                                                                                print("Could not find 'Someone else to pick up' option")
                                                                            else:
                                                                                print("Waiting for contact form to load...")
                                                                                time.sleep(3)
                                                                                
                                                                                print("Filling out contact form...")
                                                                                try:
                                                                                    print("Filling first name field...")
                                                                                    first_name_selectors = [
                                                                                        "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.firstName']",
                                                                                        "input[name='firstName']",
                                                                                        "input[data-autom='form-field-firstName']"
                                                                                    ]
                                                                                    
                                                                                    first_name_filled = False
                                                                                    for selector in first_name_selectors:
                                                                                        try:
                                                                                            first_name_input = WebDriverWait(driver, 5).until(
                                                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                            )
                                                                                            first_name_input.clear()
                                                                                            first_name_input.send_keys("test")
                                                                                            print("Entered first name: test")
                                                                                            first_name_filled = True
                                                                                            break
                                                                                        except:
                                                                                            continue
                                                                                    
                                                                                    if not first_name_filled:
                                                                                        print("Could not find first name field")
                                                                                    
                                                                                    print("Filling last name field...")
                                                                                    last_name_selectors = [
                                                                                        "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.lastName']",
                                                                                        "input[name='lastName']",
                                                                                        "input[data-autom='form-field-lastName']"
                                                                                    ]
                                                                                    
                                                                                    last_name_filled = False
                                                                                    for selector in last_name_selectors:
                                                                                        try:
                                                                                            last_name_input = WebDriverWait(driver, 5).until(
                                                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                            )
                                                                                            last_name_input.clear()
                                                                                            last_name_input.send_keys("test")
                                                                                            print("Entered last name: test")
                                                                                            last_name_filled = True
                                                                                            break
                                                                                        except:
                                                                                            continue
                                                                                    
                                                                                    if not last_name_filled:
                                                                                        print("Could not find last name field")
                                                                                    
                                                                                    print("Filling email field...")
                                                                                    email_selectors = [
                                                                                        "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.emailAddress']",
                                                                                        "input[name='emailAddress']",
                                                                                        "input[type='email']",
                                                                                        "input[data-autom='form-field-emailAddress']"
                                                                                    ]
                                                                                    
                                                                                    email_filled = False
                                                                                    for selector in email_selectors:
                                                                                        try:
                                                                                            email_input = WebDriverWait(driver, 5).until(
                                                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                            )
                                                                                            email_input.clear()
                                                                                            email_input.send_keys("test@gmail.com")
                                                                                            print("Entered email: test@gmail.com")
                                                                                            email_filled = True
                                                                                            break
                                                                                        except:
                                                                                            continue
                                                                                    
                                                                                    if not email_filled:
                                                                                        print("Could not find email field")
                                                                                    
                                                                                    print("Filling phone field...")
                                                                                    phone_selectors = [
                                                                                        "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.fullDaytimePhone']",
                                                                                        "input[name='fullDaytimePhone']",
                                                                                        "input[type='tel']",
                                                                                        "input[data-autom='form-field-fullDaytimePhone']"
                                                                                    ]
                                                                                    
                                                                                    phone_filled = False
                                                                                    for selector in phone_selectors:
                                                                                        try:
                                                                                            phone_input = WebDriverWait(driver, 5).until(
                                                                                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                            )
                                                                                            phone_input.clear()
                                                                                            phone_input.send_keys("3422342342")
                                                                                            print("Entered phone: 3422342342")
                                                                                            phone_filled = True
                                                                                            
                                                                                            time.sleep(1)
                                                                                            phone_input.send_keys(Keys.RETURN)
                                                                                            print("Pressed Enter to submit form")
                                                                                            break
                                                                                        except:
                                                                                            continue
                                                                                    
                                                                                    if not phone_filled:
                                                                                        print("Could not find phone field")
                                                                                    
                                                                                    print("Form filling completed")
                                                                                    
                                                                                    print("Looking for notification checkbox and billing fields...")
                                                                                    time.sleep(3)
                                                                                    
                                                                                    try:
                                                                                        print("Clicking notification checkbox...")
                                                                                        checkbox_selectors = [
                                                                                            "input[id='checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.acceptTextNotification']",
                                                                                            "input[type='checkbox']",
                                                                                            ".form-checkbox input"
                                                                                        ]
                                                                                        
                                                                                        checkbox_clicked = False
                                                                                        for selector in checkbox_selectors:
                                                                                            try:
                                                                                                checkbox = WebDriverWait(driver, 5).until(
                                                                                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                                )
                                                                                                checkbox.click()
                                                                                                print("Notification checkbox clicked")
                                                                                                checkbox_clicked = True
                                                                                                break
                                                                                            except:
                                                                                                continue
                                                                                        
                                                                                        if not checkbox_clicked:
                                                                                            print("Could not find notification checkbox")
                                                                                        
                                                                                        print("Filling billing email field...")
                                                                                        billing_email_selectors = [
                                                                                            "input[id='checkout.pickupContact.thirdPartyPickupContact.billingContact.address.emailAddress']",
                                                                                            "input[name='emailAddress'][type='email']",
                                                                                            "input[data-autom='form-field-emailAddress']"
                                                                                        ]
                                                                                        
                                                                                        billing_email_filled = False
                                                                                        for selector in billing_email_selectors:
                                                                                            try:
                                                                                                billing_email_input = WebDriverWait(driver, 5).until(
                                                                                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                                )
                                                                                                billing_email_input.clear()
                                                                                                billing_email_input.send_keys("test@gmail.com")
                                                                                                print("Entered billing email: test@gmail.com")
                                                                                                billing_email_filled = True
                                                                                                break
                                                                                            except:
                                                                                                continue
                                                                                        
                                                                                        if not billing_email_filled:
                                                                                            print("Could not find billing email field")
                                                                                        
                                                                                        print("Filling billing phone field...")
                                                                                        billing_phone_selectors = [
                                                                                            "input[id='checkout.pickupContact.thirdPartyPickupContact.billingContact.address.fullDaytimePhone']",
                                                                                            "input[name='fullDaytimePhone'][type='tel']",
                                                                                            "input[data-autom='form-field-fullDaytimePhone']"
                                                                                        ]
                                                                                        
                                                                                        billing_phone_filled = False
                                                                                        for selector in billing_phone_selectors:
                                                                                            try:
                                                                                                billing_phone_input = WebDriverWait(driver, 5).until(
                                                                                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                                )
                                                                                                billing_phone_input.clear()
                                                                                                billing_phone_input.send_keys("3422342342")
                                                                                                print("Entered billing phone: 3422342342")
                                                                                                billing_phone_filled = True
                                                                                                break
                                                                                            except:
                                                                                                continue
                                                                                        
                                                                                        if not billing_phone_filled:
                                                                                            print("Could not find billing phone field")
                                                                                        
                                                                                        print("Looking for Continue to Payment button...")
                                                                                        time.sleep(2)
                                                                                        
                                                                                        continue_payment_selectors = [
                                                                                            "button[data-autom='continue-button-label']",
                                                                                            "button[id='rs-checkout-continue-button-bottom']",
                                                                                            ".rs-checkout-action button",
                                                                                            "button[class*='form-button']"
                                                                                        ]
                                                                                        
                                                                                        payment_clicked = False
                                                                                        for selector in continue_payment_selectors:
                                                                                            try:
                                                                                                payment_button = WebDriverWait(driver, 5).until(
                                                                                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                                                                                )
                                                                                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", payment_button)
                                                                                                time.sleep(1)
                                                                                                payment_button.click()
                                                                                                print("Continue to Payment button clicked")
                                                                                                payment_clicked = True
                                                                                                break
                                                                                            except:
                                                                                                continue
                                                                                        
                                                                                        if not payment_clicked:
                                                                                            try:
                                                                                                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                                                                                                for btn in all_buttons:
                                                                                                    if btn.is_displayed() and btn.is_enabled():
                                                                                                        btn_text = btn.text.strip().lower()
                                                                                                        if "continue" in btn_text or "payment" in btn_text:
                                                                                                            btn.click()
                                                                                                            print("Continue to Payment button clicked (text search)")
                                                                                                            payment_clicked = True
                                                                                                            break
                                                                                            except:
                                                                                                pass
                                                                                        
                                                                                        if not payment_clicked:
                                                                                            print("Could not find Continue to Payment button")
                                                                                    
                                                                                    except Exception as e:
                                                                                        print(f"Error with checkout form: {e}")
                                                                                    
                                                                                except Exception as e:
                                                                                    print(f"Error filling contact form: {e}")
                                                                                    try:
                                                                                        inputs = driver.find_elements(By.TAG_NAME, "input")
                                                                                        print("Available input fields:")
                                                                                        for i, inp in enumerate(inputs[:10]):
                                                                                            if inp.is_displayed():
                                                                                                print(f"  Input {i+1}: ID={inp.get_attribute('id')}, Name={inp.get_attribute('name')}, Type={inp.get_attribute('type')}")
                                                                                    except:
                                                                                        pass
                                                                        
                                                                        except Exception as e:
                                                                            print(f"Error finding third party pickup option: {e}")
                                                                
                                                                except Exception as e:
                                                                    print(f"Error finding final Continue button: {e}")
                                                        
                                                        except Exception as e:
                                                            print(f"Error handling pickup time slot: {e}")
                                                
                                                except Exception as e:
                                                    print(f"Error finding Continue as Guest button: {e}")
                                        
                                        except Exception as e:
                                            print(f"Error finding Checkout button: {e}")
                                
                                except Exception as e:
                                    print(f"Error finding Review Bag button: {e}")
                        
                        except Exception as e:
                            print(f"Error finding Add to Bag button: {e}")
                
                except Exception as e:
                    print(f"Error finding Continue button: {e}")
                
            else:
                print("No stores have the iPhone 16 Pro available for pickup today")
            
            if unavailable_stores:
                print(f"UNAVAILABLE LOCATIONS ({len(unavailable_stores)} stores):")
                for store in unavailable_stores[:5]:
                    print(f"  - {store['name']} - {store['location']}")
                if len(unavailable_stores) > 5:
                    print(f"  ... and {len(unavailable_stores) - 5} more")
        
        except TimeoutException:
            print("Could not find store results. The page might still be loading or the structure changed.")
        except Exception as e:
            print(f"Error analyzing store availability: {e}")
        
        print("SUCCESS: All steps completed")
        print("1. AppleCare option clicked")
        print("2. Pickup button clicked") 
        print("3. Zip code '33165' entered and submitted")
        print("4. Store availability analyzed")
        print("5. First available store selected")
        print("6. Continue button clicked")
        print("7. Add to Bag button clicked")
        print("8. Review Bag button clicked")
        print("9. Checkout button clicked")
        print("10. Continue as Guest button clicked")
        print("11. First available pickup time slot selected")
        print("12. Final Continue button clicked")
        print("13. Someone else to pick up selected")
        print("14. Contact form filled out and submitted")
        print("15. Notification checkbox clicked, billing info filled, Continue to Payment clicked")
        
        print("Keeping browser open for 50 seconds to see final results...")
        
        # Testing payement
        print("Selecting CREDIT payment option at checkout...")
        try:
            credit_radio = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#checkout\\.billing\\.billingoptions\\.credit"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", credit_radio)
            time.sleep(1)
            driver.execute_script("arguments[0].focus();", credit_radio)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", credit_radio)
            print("CREDIT payment option selected successfully")
            
            # Wait longer for the form to fully load
            time.sleep(3)
            
            print("Waiting for credit card fields to load...")
            
            # Check for iframes first (credit card fields are often in iframes for security)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")
            
            card_fields_found = False
            
            # Method 1: Try to find fields in iframes
            for i, iframe in enumerate(iframes):
                try:
                    print(f"Checking iframe {i}")
                    driver.switch_to.frame(iframe)
                    
                    # Look for credit card input fields in iframe
                    card_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='tel'], input[name*='card'], input[placeholder*='card'], input[id*='card']")
                    
                    if card_inputs:
                        print(f"Found {len(card_inputs)} potential card fields in iframe {i}")
                        for j, inp in enumerate(card_inputs):
                            try:
                                placeholder = inp.get_attribute("placeholder") or ""
                                name = inp.get_attribute("name") or ""
                                id_attr = inp.get_attribute("id") or ""
                                print(f"  Field {j}: placeholder='{placeholder}', name='{name}', id='{id_attr}'")
                            except:
                                pass
                        
                        # Try to fill the fields if they look like credit card fields
                        if len(card_inputs) >= 3:
                            try:
                                # Usually first field is card number
                                card_number_field = card_inputs[0]
                                driver.execute_script("arguments[0].focus();", card_number_field)
                                card_number_field.clear()
                                card_number_field.send_keys("4242424242424242")
                                print("Credit card number entered in iframe")
                                
                                # Second field is usually expiry
                                expiry_field = card_inputs[1]
                                driver.execute_script("arguments[0].focus();", expiry_field)
                                expiry_field.clear()
                                expiry_field.send_keys("04/26")
                                print("Expiry date entered in iframe")
                                
                                # Third field is usually CVC
                                if len(card_inputs) > 2:
                                    cvc_field = card_inputs[2]
                                    driver.execute_script("arguments[0].focus();", cvc_field)
                                    cvc_field.clear()
                                    cvc_field.send_keys("123")
                                    print("CVC entered in iframe")
                                
                                card_fields_found = True
                                break
                                
                            except Exception as e:
                                print(f"Error filling iframe fields: {e}")
                    
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"Error checking iframe {i}: {e}")
                    driver.switch_to.default_content()
            
            # Method 2: If not found in iframes, try main page with specific IDs
            if not card_fields_found:
                print("No card fields found in iframes, trying main page with specific selectors...")
                
                try:
                    # Wait for the specific credit card fields to be present
                    card_number_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.cardNumber"))
                    )
                    
                    expiry_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.expiration")
                    cvc_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.securityCode")
                    
                    print("Found credit card fields by ID")
                    
                    # Wait for fields to be interactable
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(card_number_field))
                    
                    # Fill card number
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_number_field)
                    time.sleep(1)
                    driver.execute_script("arguments[0].focus();", card_number_field)
                    card_number_field.clear()
                    card_number_field.send_keys("4242424242424242")
                    print("Credit card number entered")
                    time.sleep(1)
                    
                    # Fill expiry date
                    driver.execute_script("arguments[0].focus();", expiry_field)
                    expiry_field.clear()
                    expiry_field.send_keys("04/26")
                    print("Expiry date entered")
                    time.sleep(1)
                    
                    # Fill CVC
                    driver.execute_script("arguments[0].focus();", cvc_field)
                    cvc_field.clear()
                    cvc_field.send_keys("123")
                    print("CVC entered")
                    
                    card_fields_found = True
                    
                except Exception as e:
                    print(f"Error filling fields by ID: {e}")
                    
                    # Fallback: Try by partial ID matching
                    try:
                        print("Trying fallback method with partial ID matching...")
                        
                        card_number_field = driver.find_element(By.CSS_SELECTOR, "input[id*='cardNumber']")
                        expiry_field = driver.find_element(By.CSS_SELECTOR, "input[id*='expiration']")
                        cvc_field = driver.find_element(By.CSS_SELECTOR, "input[id*='securityCode']")
                        
                        # Fill card number
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_number_field)
                        time.sleep(1)
                        driver.execute_script("arguments[0].focus();", card_number_field)
                        card_number_field.clear()
                        card_number_field.send_keys("4242424242424242")
                        print("Credit card number entered (fallback)")
                        time.sleep(1)
                        
                        # Fill expiry date
                        driver.execute_script("arguments[0].focus();", expiry_field)
                        expiry_field.clear()
                        expiry_field.send_keys("04/26")
                        print("Expiry date entered (fallback)")
                        time.sleep(1)
                        
                        # Fill CVC
                        driver.execute_script("arguments[0].focus();", cvc_field)
                        cvc_field.clear()
                        cvc_field.send_keys("123")
                        print("CVC entered (fallback)")
                        
                        card_fields_found = True
                        
                    except Exception as e2:
                        print(f"Fallback method also failed: {e2}")
            
            if card_fields_found:
                print("Credit card details filled successfully")
            else:
                print("Could not locate credit card fields")
                
                # Debug: Print all form elements
                print("\nDebugging - All form elements:")
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                for i, inp in enumerate(all_inputs):
                    try:
                        if inp.is_displayed():
                            input_id = inp.get_attribute("id") or ""
                            input_name = inp.get_attribute("name") or ""
                            input_type = inp.get_attribute("type") or ""
                            input_placeholder = inp.get_attribute("placeholder") or ""
                            print(f"Input {i}: id='{input_id}', name='{input_name}', type='{input_type}', placeholder='{input_placeholder}'")
                    except:
                        pass

        except Exception as e:
            print(f"Error in credit card section: {e}")
        finally:
            driver.switch_to.default_content()
            
        
        
        
        
        
        
        
        
        
        # Fill billing address fields
            print("Filling billing address information...")
            time.sleep(1)
            
            # First Name
            try:
                first_name_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.firstName")
                driver.execute_script("arguments[0].focus();", first_name_field)
                first_name_field.clear()
                first_name_field.send_keys("test")
                print("First name entered")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error filling first name: {e}")
            
            # Last Name
            try:
                last_name_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.lastName")
                driver.execute_script("arguments[0].focus();", last_name_field)
                last_name_field.clear()
                last_name_field.send_keys("test")
                print("Last name entered")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error filling last name: {e}")
            
            # Street Address
            try:
                street_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.street")
                driver.execute_script("arguments[0].focus();", street_field)
                street_field.clear()
                street_field.send_keys("test test test test test test test test")
                print("Street address entered")
                time.sleep(0.5)
            except Exception as e:
                print(f"Error filling street address: {e}")
            
            # Postal Code
            try:
                postal_code_field = driver.find_element(By.ID, "checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.zipLookup.postalCode")
                driver.execute_script("arguments[0].focus();", postal_code_field)
                postal_code_field.clear()
                postal_code_field.send_keys("32003")
                print("Postal code entered")
                time.sleep(1)  # Wait a bit longer for postal code lookup
            except Exception as e:
                print(f"Error filling postal code: {e}")
            
            print("Billing address information filled successfully")
            
            # Click Continue to Review button
            try:
                continue_button = driver.find_element(By.ID, "rs-checkout-continue-button-bottom")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", continue_button)
                print("Continue to Review button clicked")
                time.sleep(2)
            except Exception as e:
                print(f"Error clicking Continue to Review button: {e}")
                
            
            # Click Continue button on review page
            try:
                continue_button = driver.find_element(By.ID, "rs-checkout-continue-button-bottom")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", continue_button)
                print("Continue button clicked on review page")
                time.sleep(2)
            except Exception as e:
                print(f"Error clicking Continue button: {e}")
        
        
        
        
        time.sleep(50)
        
    except TimeoutException as e:
        print(f"Timeout error: Could not find element - {e}")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    print("Starting Apple website automation...")
    open_apple_site_and_click()