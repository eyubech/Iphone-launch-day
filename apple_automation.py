import os
import re
import time
import sys
import traceback
import logging

logging.basicConfig(level=logging.INFO)

from seleniumwire import webdriver as wire_webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)

from config import Config

try:
    from email_manager import EmailManager
except Exception:
    EmailManager = None


class AppleAutomation:
    def __init__(
        self,
        card_data=None,
        person_data=None,
        settings_data=None,
        user_data=None,
        proxy_session=None,
        auto_restart=None,
        max_runs=None,
        *,
        product_url=None,
        use_proxy=None,
        process_num=None,
    ):
        self.config = Config()
        self.driver = None
        self._stopped = False

        if product_url:
            self.config.PRODUCT_URL = product_url

        self.use_proxy = (bool(int(os.environ.get("USE_PROXY", "0"))) if use_proxy is None
                  else bool(use_proxy))
        self.secure_direct_proxy = bool(getattr(self.config, "SECURE_DIRECT_PROXY", True))

        self.process_num = int(process_num) if process_num is not None else os.getpid()

        self.purchase_count = 0
        self.max_purchases = 2
        self.saved_link = ""

        self.proxy_session = proxy_session or "initial"
        self.auto_restart = (getattr(self.config, "AUTO_RESTART", False) if auto_restart is None
                else bool(auto_restart))
        self.max_runs = (getattr(self.config, "MAX_RUNS", 1) if max_runs is None
                else int(max_runs))

        self.email_manager = EmailManager() if EmailManager else None
        self.process_email = None

        if card_data and person_data and settings_data:
            self.user_data = self._combine_automation_data(card_data, person_data, settings_data)
            self.card_data = card_data
        elif user_data:
            self.user_data = user_data
            self.card_data = {}
        else:
            self.user_data = self.config.DEFAULT_VALUES
            self.card_data = {}

    def _build_oxylabs_proxy_url(self):
        user_base = os.getenv("OXY_USER_BASE") or getattr(self.config, "OXY_USER_BASE", "")
        password  = os.getenv("OXY_PASS")      or getattr(self.config, "OXY_PASS", "")
        entry     = os.getenv("OXY_ENTRY")     or getattr(self.config, "OXY_ENTRY", "us-pr.oxylabs.io")
        port      = int(os.getenv("OXY_PORT")  or getattr(self.config, "OXY_PORT", 10000))
        city      = (os.getenv("OXY_CITY")     or getattr(self.config, "OXY_CITY", "")).strip().lower().replace(" ", "_")
        state     = (os.getenv("OXY_STATE")    or getattr(self.config, "OXY_STATE", "")).strip().lower().replace(" ", "_")
        sessid    = os.getenv("OXY_SESSID")    or f"{os.getpid()}_{int(time.time())}"

        parts = [f"customer-{user_base}"]
        if city:
            parts.append(f"city-{city}")
        elif state:
            parts.append(f"st-us_{state}")
        parts.append(f"sessid-{sessid}")

        username = "-".join(parts)
        return f"http://{username}:{password}@{entry}:{port}"

    def setup_driver(self):
        from selenium import webdriver

        opts = ChromeOptions()
        for o in getattr(self.config, "BROWSER_OPTIONS", []):
            opts.add_argument(o)
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1400,1000")
        opts.add_argument("--disable-background-networking")
        opts.add_argument("--disable-sync")
        opts.add_argument("--metrics-recording-only")
        opts.add_argument("--no-first-run")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--lang=en-US,en;q=0.9")
        opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            if self.use_proxy:
                ox_user_base = os.environ.get("OXY_USER_BASE", getattr(self.config, "OXY_USER_BASE", "garrajemobile_uKxOe"))
                ox_pass      = os.environ.get("OXY_PASS",      getattr(self.config, "OXY_PASS", "ev3FJequ_m7pHt7"))
                ox_ep        = os.environ.get("OXY_ENDPOINT",  getattr(self.config, "OXY_ENDPOINT", "us-pr.oxylabs.io"))
                ox_port      = int(os.environ.get("OXY_PORT",  getattr(self.config, "OXY_PORT", 10000)))
                ox_city      = os.environ.get("OXY_CITY")
                ox_state     = os.environ.get("OXY_STATE")
                ox_sessid    = os.environ.get("OXY_SESSID")

                user_parts = [f"customer-{ox_user_base}"]
                if ox_city:   user_parts.append(f"city-{ox_city}")
                if ox_state:  user_parts.append(f"state-{ox_state}")
                if ox_sessid: user_parts.append(f"sessid-{ox_sessid}")
                proxy_user = "-".join(user_parts)

                proxy_url = f"http://{proxy_user}:{ox_pass}@{ox_ep}:{ox_port}"
                logging.info(f"[{self.process_num}] Using selenium-wire with proxy: {ox_ep}:{ox_port}")

                self.proxy_options = {
                    "mitm_http2": False,
                    "verify_ssl": False,
                    "connection_timeout": 25,
                    "proxy": {
                        "http":  proxy_url,
                        "https": proxy_url,
                        "no_proxy": "localhost,127.0.0.1,<local>"
                    },
                }
                self.driver = wire_webdriver.Chrome(options=opts, seleniumwire_options=self.proxy_options)
            else:
                self.driver = webdriver.Chrome(options=opts)

            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = { runtime: {} };
                    """
                })
            except Exception:
                pass

            if self.use_proxy:
                try:
                    self.driver.set_page_load_timeout(max(25, getattr(self.config, "PAGE_LOAD_TIMEOUT", 25)))
                    for url in ("http://api.ipify.org?format=json", "https://api.ipify.org?format=json"):
                        self.driver.get(url)
                        time.sleep(1.0)
                        body = self.driver.find_element(By.TAG_NAME, "body").text[:250]
                        logging.info(f"[{self.process_num}] {url.split('/')[2]}: {body}")
                    logging.info(f"[{self.process_num}] Proxy reachable.")
                except Exception as e:
                    logging.warning(f"[{self.process_num}] Proxy test failed (continuing): {e}")

            return True
        except Exception as e:
            logging.error(f"[{self.process_num}] Failed to setup driver: {e}")
            return False

    def rotate_ip(self, reason="manual-rotate"):
        if not self.use_proxy:
            logging.info("Proxy disabled; rotation skipped.")
            return False
        
        logging.info(f"[{self.process_num}] IP rotation not needed with selenium-wire unless session changes.")
        return True

    def stop(self):
        self._stopped = True
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def _wait_clickable(self, by, sel, timeout=15):
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, sel)))

    def _scroll_center(self, el):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass

    def _safe_click(self, el, name="element"):
        try:
            self._scroll_center(el)
            time.sleep(0.05)
            el.click()
            logging.info(f"{name} clicked")
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", el)
                logging.info(f"{name} clicked via JS")
                return True
            except Exception as e2:
                logging.error(f"Click failed on {name}: {e2}")
                return False
        except Exception as e:
            try:
                self.driver.execute_script("arguments[0].click();", el)
                logging.info(f"{name} clicked via JS")
                return True
            except Exception:
                logging.error(f"Click failed on {name}: {e}")
                return False

    def _type_slow(self, el, text, delay=0.06):
        for ch in str(text):
            el.send_keys(ch)
            time.sleep(delay)

    def _fill_text(self, selectors, value, label="field", timeout=8):
        for sel in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                self._scroll_center(el)
                try:
                    el.clear()
                except Exception:
                    pass

                self._type_slow(el, value)

                try:
                    cur = el.get_attribute("value") or ""
                    if cur.strip() != str(value).strip():
                        self.driver.execute_script(
                            "arguments[0].value = arguments[1];"
                            "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                            el, value,
                        )
                except Exception:
                    pass
                logging.info(f"{label} filled via {sel}")
                return True
            except Exception:
                continue
        logging.error(f"Could not fill {label}")
        return False

    def _combine_automation_data(self, card_data, person_data, settings_data):
        user_info = card_data.get("user_info", {}) if card_data else {}
        return {
            "zip_code": settings_data.get("zip_code") or self.config.DEFAULT_VALUES["zip_code"],
            "street_address": settings_data.get("street_address", self.config.DEFAULT_VALUES["street_address"]),
            "postal_code": settings_data.get("postal_code", self.config.DEFAULT_VALUES["postal_code"]),
            "first_name": user_info.get("first_name", person_data.get("first_name", self.config.DEFAULT_VALUES["first_name"])),
            "last_name":  user_info.get("last_name",  person_data.get("last_name",  self.config.DEFAULT_VALUES["last_name"])),
            "email":      user_info.get("email",      person_data.get("email",      self.config.DEFAULT_VALUES["email"])),
            "phone":      user_info.get("phone",      person_data.get("phone",      self.config.DEFAULT_VALUES["phone"])),
        }

    def click_applecare_no_coverage(self):
        if self._stopped:
            return False
        logging.info("Selecting 'No AppleCare'")
        try:
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[name='applecare-options']")
            if radios:
                target = None
                for r in radios:
                    val = (r.get_attribute("value") or "").lower()
                    if "no" in val or "none" in val:
                        target = r
                        break
                if not target:
                    target = radios[-1]
                return self._safe_click(target, "No AppleCare (last radio)")
        except Exception:
            pass

        for selector in [
            "[class*='applecare'][class*='no']",
            "[data-autom*='noapple']",
            "input[type='radio'][value*='no']",
            "label[for*='applecare'][for*='no']",
        ]:
            try:
                el = self._wait_clickable(By.CSS_SELECTOR, selector, 5)
                if self._safe_click(el, "No AppleCare"):
                    time.sleep(1.2)
                    return True
            except Exception:
                continue
        logging.error("Could not select No AppleCare")
        return False

    def add_to_bag(self):
        if self._stopped:
            return False
        logging.info(f"Add iPhone {self.purchase_count + 1} to bag")
        selectors = [
            'button[name="add-to-cart"]',
            'button[data-autom="add-to-cart"]',
            ".as-purchaseinfo-button button",
            'form button[type="submit"]',
            'button[class*="add-to-cart"]',
        ]
        for sel in selectors:
            try:
                el = self._wait_clickable(By.CSS_SELECTOR, sel, 12)
                if self._safe_click(el, "Add to Bag"):
                    time.sleep(2.5)
                    return True
            except Exception:
                continue
        logging.error("Add to Bag button not found")
        return False

    def handle_bag_page(self):
        if self._stopped:
            return False
        logging.info("Processing bag page")
        time.sleep(2.0)
        self.purchase_count += 1
        logging.info(f"iPhone {self.purchase_count} added")

        if self.purchase_count < self.max_purchases:
            logging.info("Going back for the next iPhone")
            try:
                self.driver.get(self.saved_link)
                WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(1.2)
                return self.run_purchase_flow()
            except Exception as e:
                logging.error(f"Error returning to product page: {e}")
                return False

        logging.info("Both iPhones added - opening Bag and proceeding to checkout")
        try:
            self.driver.get("https://www.apple.com/shop/bag")
            WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1.0)
            return self.proceed_to_checkout()
        except Exception as e:
            logging.error(f"Bag page error: {e}")
            return False

    def _dismiss_banners(self):
        for sel in [
            "[data-autom='close-cta']",
            "button[aria-label*='close' i]",
            "[data-autom*='cookie' i] button",
            "[role='dialog'] button",
            "button[aria-label*='dismiss' i]",
        ]:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                self._safe_click(el, "dismiss overlay")
                time.sleep(0.3)
            except Exception:
                pass        

    def _try_click_many(self, label, css=None, xpaths=None, timeout=12):
        css = css or []
        xpaths = xpaths or []
        for sel in css:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                self._scroll_center(el)
                if self._safe_click(el, label):
                    return True
            except Exception:
                pass
        for xp in xpaths:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self._scroll_center(el)
                if self._safe_click(el, label):
                    return True
            except Exception:
                pass
        return False

    def _click_text_anywhere(self, phrases, timeout=18):
        phrases = [p.lower() for p in phrases]
        end = time.time() + timeout
        while time.time() < end:
            t = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
            xp = " | ".join(
                [f"//button[contains({t},'{p}')]" for p in phrases] +
                [f"//a[contains({t},'{p}')]" for p in phrases]
            )
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    if el.is_displayed() and el.is_enabled():
                        self._scroll_center(el)
                        try:
                            el.click()
                            return True
                        except Exception:
                            pass
            except Exception:
                pass

            try:
                clicked = self.driver.execute_script("""
                    const needles = arguments[0];
                    function* allNodes(root){
                      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
                      let n; while(n = walker.nextNode()){
                        yield n;
                        if (n.shadowRoot) yield* allNodes(n.shadowRoot);
                      }
                    }
                    for (const el of allNodes(document)){
                      const txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                      const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                      if (!txt && !aria) continue;
                      if (needles.some(n => txt.includes(n) || aria.includes(n))){
                        el.scrollIntoView({block:'center'}); el.click(); return true;
                      }
                    }
                    return false;
                """, phrases)
                if clicked:
                    return True
            except Exception:
                pass
            time.sleep(0.4)
        return False

    def proceed_to_checkout(self):
        if self._stopped:
            return False
        logging.info("Proceeding to checkout")

        self._dismiss_banners()

        css = [
            "button#shoppingCart\\.actions\\.navCheckoutOtherPayments",
            "button[data-autom='checkout']",
            "button[data-autom*='proceed']",
            ".rs-bag-checkoutbutton button",
            ".button.button-block[data-autom='proceed']",
        ]
        t = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        xps = [
            f"//button[@id='shoppingCart.actions.navCheckoutOtherPayments']",
            f"//button[@data-autom='checkout']",
            f"//button[contains({t},'check out')]",
            f"//a[contains({t},'check out')]",
        ]

        if self._try_click_many("Check Out", css=css, xpaths=xps, timeout=15) or \
           self._click_text_anywhere(["check out", "checkout", "proceed to checkout"], timeout=10):
            time.sleep(2.0)
            return self.handle_checkout_flow()

        try:
            self.driver.get("https://secure6.store.apple.com/shop/checkout")
            WebDriverWait(self.driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return self.handle_checkout_flow()
        except Exception:
            pass

        logging.error("Checkout proceed button not found")
        return False

    def handle_checkout_flow(self):
        if self._stopped:
            return False
        logging.info("Handling checkout page")

        def on_checkout():
            try:
                return "/shop/checkout" in (self.driver.current_url or "").lower()
            except Exception:
                return False

        try:
            self._dismiss_banners()
        except Exception:
            pass

        try:
            if self.driver.find_elements(By.ID, "signIn.guestLogin.guestLogin") or \
               self.driver.find_elements(By.CSS_SELECTOR, "[data-autom='guest-checkout-btn']"):
                return self.handle_guest_login()
        except Exception:
            pass

        if not on_checkout():
            hosts = (
                "secure6.store.apple.com",
                "secure7.store.apple.com",
                "secure8.store.apple.com",
                "secure.store.apple.com",
            )
            for host in hosts:
                try:
                    self.driver.get(f"https://{host}/shop/checkout")
                    WebDriverWait(self.driver, 15).until(lambda d: "/shop/checkout" in d.current_url.lower())
                    break
                except Exception:
                    continue

        try:
            self._dismiss_banners()
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, 12).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "signIn.guestLogin.guestLogin")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-autom='guest-checkout-btn']")),
                    EC.presence_of_element_located((By.XPATH,
                        "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'guest checkout')]")),
                )
            )
        except Exception:
            pass

        return self.handle_guest_login()    

    def handle_guest_login(self):
        if self._stopped:
            return False
        logging.info("Continuing as guest")

        self._dismiss_banners()

        try:
            WebDriverWait(self.driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "signIn.guestLogin.guestLogin")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-autom='guest-checkout-btn']")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'guest checkout')]")),
                )
            )
        except Exception:
            pass

        css = [
            "button#signIn\\.guestLogin\\.guestLogin",
            "button[data-autom='guest-checkout-btn']",
            ".rs-guest-checkout button[data-autom='guest-checkout-btn']",
            ".form-button[data-autom='guest-checkout-btn']",
        ]
        t = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        xps = [
            f"//button[@id='signIn.guestLogin.guestLogin']",
            f"//button[@data-autom='guest-checkout-btn']",
            f"//button[contains({t},'continue as guest')]",
            f"//a[contains({t},'continue as guest')]",
            f"//*[@class and contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'guest')]//button",
        ]

        if self._try_click_many("Continue as Guest", css=css, xpaths=xps, timeout=15) or \
           self._click_text_anywhere(["continue as guest", "guest checkout"], timeout=12):
            time.sleep(3.5)
            return self.handle_pickup_section()

        logging.error("Guest checkout button not found")
        return False

    def handle_pickup_section(self):
        if self._stopped:
            return False
        logging.info("Looking for pickup button (segmented control)")
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
                logging.info(f"Looking for pickup buttons with selector: {selector}")
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                logging.info(f"Found {len(buttons)} segmented control buttons")
                
                if len(buttons) >= 2:
                    pickup_button = buttons[1]
                    logging.info("Attempting to click second segmented button (pickup)")
                    
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
                            logging.info(f"Trying {method_name}")
                            method()
                            time.sleep(2)
                            
                            button_class = pickup_button.get_attribute('class')
                            aria_checked = pickup_button.get_attribute('aria-checked')
                            
                            if 'selected' in button_class or aria_checked == 'true':
                                logging.info(f"Pickup button clicked successfully using {method_name}")
                                logging.info(f"Button class: {button_class}")
                                logging.info(f"Aria-checked: {aria_checked}")
                                time.sleep(3)
                                return self.handle_zip_code_input()
                            else:
                                logging.info(f"{method_name} - no state change detected")
                        except Exception as e:
                            logging.info(f"{method_name} failed: {e}")
                            continue
                    
                    logging.info("All click methods failed for pickup button")
                    return False
                    
            except Exception as e:
                logging.info(f"Selector {selector} failed: {e}")
                continue
        
        logging.error("Could not find pickup segmented control buttons")
        return False

    def handle_zip_code_input(self):
        if self._stopped:
            return False
        logging.info("Entering ZIP and searching stores")

        try:
            edit_btn = WebDriverWait(self.driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-autom='fulfillment-pickup-store-search-button']"))
            )
            self._safe_click(edit_btn, "Edit location")
            time.sleep(0.8)
        except Exception:
            pass

        input_selectors = [
            "#checkout\\.fulfillment\\.pickupTab\\.pickup\\.storeLocator\\.searchInput",
            "[data-autom='bag-storelocator-input']",
            "input[aria-labelledby='checkout.fulfillment.pickupTab.pickup.storeLocator.searchInput_label']",
            "input.form-textbox-input[role='combobox']",
            "input[placeholder*='ZIP' i]",
            "input[placeholder*='postal' i]",
            "input[name*='zip' i]",
            "input[id*='zip' i]"
        ]

        zip_input = None
        for selector in input_selectors:
            try:
                zip_input = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logging.info(f"Found ZIP input using selector: {selector}")
                break
            except Exception:
                continue

        if not zip_input:
            logging.error("ZIP input field not found with any selector")
            return False

        zip_code = str(self.user_data["zip_code"]).strip()
        logging.info(f"Entering ZIP code: {zip_code}")

        try:
            self._scroll_center(zip_input)
            time.sleep(0.2)
            zip_input.click()
            time.sleep(0.3)
        except Exception as e:
            logging.error(f"Error focusing ZIP input: {e}")

        try:
            zip_input.click()
            time.sleep(0.3)
            
            zip_input.send_keys(Keys.CONTROL + 'a')
            time.sleep(0.2)
            zip_input.send_keys(Keys.DELETE)
            time.sleep(0.3)
            
            zip_input.clear()
            time.sleep(0.5)
            
            zip_input.send_keys(zip_code)
            logging.info(f"ZIP code entered: {zip_code}")
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Error entering ZIP code: {e}")
            return False

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
                logging.info(f"Looking for apply button with selector: {apply_selector}")
                apply_btn = self.driver.find_element(By.CSS_SELECTOR, apply_selector)
                if apply_btn.is_displayed() and apply_btn.is_enabled():
                    apply_btn.click()
                    logging.info("Apply button clicked successfully")
                    apply_clicked = True
                    break
            except Exception as e:
                logging.info(f"Apply selector {apply_selector} failed: {e}")
                continue
        
        if not apply_clicked:
            logging.info("No apply button found, trying Enter key")
            zip_input.send_keys(Keys.ENTER)
            logging.info("Pressed Enter on zip input")

        logging.info("Waiting 5 seconds for stores to load")
        time.sleep(5)
        
        return self.validate_and_select_store()

    def validate_and_select_store(self):
        if self._stopped:
            return False
        logging.info("Validating stores")
        try:
            store_list = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.rt-storelocator-store-group.form-selector-group"))
            )
            items = store_list.find_elements(By.TAG_NAME, "li")
            logging.info(f"Found {len(items)} stores")
            if not items:
                return False
            self._scroll_center(items[0])
            items[0].click()
            time.sleep(1.2)
            return self.handle_time_slot_selection()
        except Exception as e:
            logging.error(f"Store selection error: {e}")
            return False

    def handle_time_slot_selection(self):
        if self._stopped:
            return False
        logging.info("Selecting first available time slot")

        locators = [
            (By.ID, "checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots.timeSlotValue"),
            (By.CSS_SELECTOR, "select[data-autom='pickup-availablewindow-dropdown']"),
            (By.XPATH, "//select[@required and contains(@aria-labelledby,'rs-pickup-slottitle')]"),
        ]

        select_el = None
        options = []
        for by, sel in locators:
            try:
                select_el = WebDriverWait(self.driver, 12).until(EC.element_to_be_clickable((by, sel)))
                self._scroll_center(select_el)
                options = [o for o in select_el.find_elements(By.TAG_NAME, "option")
                           if (o.get_attribute("value") or "").strip()]
                if options:
                    break
            except Exception:
                select_el = None

        if not select_el or not options:
            logging.error("Time slot dropdown not found/empty")
            return False

        picked = False
        try:
            sel = Select(select_el)
            for o in sel.options:
                v = (o.get_attribute("value") or "").strip()
                if v:
                    sel.select_by_value(v)
                    logging.info(f"Time slot selected via Select: {o.text}")
                    picked = True
                    break
        except Exception:
            pass

        if not picked:
            try:
                select_el.click()
                time.sleep(0.2)
                select_el.send_keys(Keys.ARROW_DOWN)
                select_el.send_keys(Keys.ENTER)
                logging.info("Time slot selected via keyboard")
                picked = True
            except Exception:
                pass

        try:
            self.driver.execute_script("""
                const s = arguments[0];
                s.dispatchEvent(new Event('input',  {bubbles:true}));
                s.dispatchEvent(new Event('change', {bubbles:true}));
            """, select_el)
            try:
                select_el.send_keys(Keys.TAB)
            except Exception:
                pass
        except Exception:
            pass

        def valid_now():
            try:
                invalid = select_el.get_attribute("aria-invalid")
                if not invalid or invalid == "false":
                    return True
                err = self.driver.find_elements(
                    By.ID,
                    "checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots.timeSlotValue_error"
                )
                return not err or not any(e.is_displayed() for e in err)
            except Exception:
                return True

        try:
            WebDriverWait(self.driver, 5).until(lambda d: valid_now())
        except Exception:
            logging.warning("Validation still flagged, continuing anyway.")

        time.sleep(0.6)
        return self.scroll_and_continue()

    def scroll_and_continue(self):
        if self._stopped:
            return False
        logging.info("Scrolling to bottom and clicking continue button")

        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)

            continue_selectors = [
                'button[id="rs-checkout-continue-button-bottom"]',
                'button[data-autom="fulfillment-continue-button"]',
                ".rs-checkout-action button",
                "button.form-button",
                'button[type="button"][class*="form-button"]',
                ".rs-checkout-action-button-wrapper button",
            ]

            for selector in continue_selectors:
                try:
                    btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self._scroll_center(btn)
                    time.sleep(0.3)
                    btn.click()
                    logging.info("Continue button clicked successfully")
                    time.sleep(1.2)
                    return self.fill_contact_forms()
                except Exception:
                    continue

            logging.error("Could not find continue button")
            return False
        except Exception as e:
            logging.error(f"Error in scroll_and_continue: {e}")
            return False

    def fill_contact_forms(self):
        if self._stopped:
            return False
        logging.info("Filling pickup contact details")

        for sel in [
            'button[data-autom="thirdPartyPickup"]',
            '.rc-segmented-control-item button[data-autom="thirdPartyPickup"]',
            'button[role="radio"][data-autom="thirdPartyPickup"]',
        ]:
            try:
                el = self._wait_clickable(By.CSS_SELECTOR, sel, 4)
                self._safe_click(el, "Third-party pickup")
                time.sleep(0.5)
                break
            except Exception:
                continue

        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.firstName"]',
                'input[name="firstName"][id*="thirdPartyContact.address.firstName"]',
            ],
            self.user_data["first_name"],
            "first name",
        )
        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.lastName"]',
                'input[name="lastName"][id*="thirdPartyContact.address.lastName"]',
            ],
            self.user_data["last_name"],
            "last name",
        )
        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.emailAddress"]',
                'input[name="emailAddress"][id*="thirdPartyContact.address.emailAddress"]',
            ],
            self.user_data["email"],
            "email",
        )
        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.address.fullDaytimePhone"]',
                'input[name="fullDaytimePhone"][id*="thirdPartyContact.address.fullDaytimePhone"]',
            ],
            self.user_data["phone"],
            "phone",
        )

        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.billingContact.address.emailAddress"]',
                'input[name="emailAddress"][id*="billingContact.address.emailAddress"]',
            ],
            self.user_data["email"],
            "billing contact email",
        )
        self._fill_text(
            [
                'input[id="checkout.pickupContact.thirdPartyPickupContact.billingContact.address.fullDaytimePhone"]',
                'input[name="fullDaytimePhone"][id*="billingContact.address.fullDaytimePhone"]',
            ],
            self.user_data["phone"],
            "billing contact phone",
        )

        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.4)
        except Exception:
            pass

        selectors = [
            'button[data-autom="continue-button-label"]',
            "#rs-checkout-continue-button-bottom",
            ".rs-checkout-action button",
        ]
        for sel in selectors:
            try:
                el = self._wait_clickable(By.CSS_SELECTOR, sel, 10)
                if self._safe_click(el, "Continue to Payment"):
                    time.sleep(1.2)
                    return self.handle_payment_form()
            except Exception:
                continue
        logging.error("Continue to Payment not found")
        return False

    _JS_SET_REACT_VALUE = """
    const el = arguments[0], val = arguments[1];
    const desc = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
    if (desc && desc.set) { desc.set.call(el, val); } else { el.value = val; }
    el.dispatchEvent(new Event('input',  {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
    el.dispatchEvent(new Event('blur',   {bubbles:true}));
    """

    def _fill_input_any(self, selectors, value, label="field", timeout=10, secure=False):
        def _find(by, sel):
            try:
                return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, sel)))
            except Exception:
                return None

        target = None
        for s in selectors:
            by = By.XPATH if s.startswith("//") else By.CSS_SELECTOR
            target = _find(by, s)
            if target: break

        if not target:
            logging.error(f"{label}: not found")
            return False

        try: self._scroll_center(target)
        except: pass

        try:
            for ch in str(value):
                target.send_keys(ch)
                time.sleep(0.015)
        except: pass
        try:
            self.driver.execute_script(self._JS_SET_REACT_VALUE, target, str(value))
        except: pass

        try: target.send_keys(Keys.TAB)
        except: pass

        logging.info(f"{label} filled{' (redacted)' if secure else ''}")
        return True

    def _select_dropdown_value(self, selectors, wanted, label="select", timeout=10):
        for s in selectors:
            by = By.XPATH if s.startswith("//") else By.CSS_SELECTOR
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, s)))
                self._scroll_center(el)
                self.driver.execute_script("""
                  const sel=arguments[0], w=arguments[1];
                  const opt=[...sel.options].find(o=>o.value===w || o.text.trim().toLowerCase()===w.toLowerCase());
                  if (opt){ sel.value = opt.value;
                    sel.dispatchEvent(new Event('input',{bubbles:true}));
                    sel.dispatchEvent(new Event('change',{bubbles:true}));
                  }
                """, el, wanted)
                logging.info(f"{label} → {wanted}")
                return True
            except Exception:
                continue
        logging.error(f"{label}: couldn't set")
        return False

    def _ensure_credit_card_selected(self, timeout=12):
        logging.info("Ensuring 'Credit or Debit Card' is selected")
        try:
            lab = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='checkout.billing.billingoptions.credit']"))
            )
            self._scroll_center(lab)
            try: lab.click()
            except: self.driver.execute_script("arguments[0].click();", lab)
        except Exception:
            for by, sel in [
                (By.CSS_SELECTOR, "input#checkout\\.billing\\.billingoptions\\.credit"),
                (By.CSS_SELECTOR, "input[data-autom='checkout-billingOptions-CREDIT']"),
                (By.XPATH, "//input[@type='radio' and @value='CREDIT']"),
            ]:
                try:
                    el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, sel)))
                    self._scroll_center(el)
                    try: el.click()
                    except: self.driver.execute_script("arguments[0].click();", el)
                    break
                except Exception:
                    continue

        try:
            radio = self.driver.find_element(By.CSS_SELECTOR, "input#checkout\\.billing\\.billingoptions\\.credit")
            self.driver.execute_script("""
              const r=arguments[0];
              r.checked=true;
              r.dispatchEvent(new Event('input',{bubbles:true}));
              r.dispatchEvent(new Event('change',{bubbles:true}));
            """, radio)
        except Exception:
            pass

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-autom='card-number-input'], [data-autom='expiration-input']"))
            )
            logging.info("Credit/Debit option active")
            return True
        except Exception:
            logging.error("Couldn't confirm Credit/Debit expanded")
            return False

    def _js_set_value(self, el, value, label="field"):
        try:
            self.driver.execute_script("""
                const el = arguments[0], val = String(arguments[1]);
                const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
                desc.set.call(el, '');
                el.dispatchEvent(new Event('input', {bubbles:true}));
                desc.set.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
            """, el, value)
            logging.info(f"{label} set via JS")
            return True
        except Exception as e:
            logging.error(f"{label} JS set failed: {e}")
            return False

    def _wait_for_confirmation(self, timeout=60):
        texpr = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        xpaths = [
            f"//*[contains({texpr},'thank you') and contains({texpr},'order')]",
            f"//*[contains({texpr},'order number')]",
            f"//*[contains({texpr},'we'') and contains({texpr},'processing your order')]",
            f"//*[contains({texpr},'confirmation')]",
        ]
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: any(len(d.find_elements(By.XPATH, xp)) > 0 for xp in xpaths)
                          or any(s in (d.current_url or '').lower() for s in [
                              "/orderrcv", "/order", "thankyou", "receipt", "confirmation"
                          ])
            )
            return True
        except Exception:
            return False

    def _is_btn_disabled(self, el):
        try:
            if el.get_attribute("disabled"):
                return True
            aria = (el.get_attribute("aria-disabled") or "").lower()
            if aria in ("true", "1"):
                return True
            cls = (el.get_attribute("class") or "").lower()
            if any(k in cls for k in ("disabled", "is-disabled", "loading", "processing")):
                return True
            style = (el.get_attribute("style") or "").lower()
            if "pointer-events: none" in style:
                return True
        except Exception:
            pass
        return False

    def _click_submit_like(self, el, name="button"):
        try:
            self._scroll_center(el)
        except Exception:
            pass

        try:
            el.click()
            logging.info(f"{name} clicked")
            return True
        except Exception:
            pass

        try:
            self.driver.execute_script("arguments[0].click();", el)
            logging.info(f"{name} clicked via JS")
            return True
        except Exception:
            pass

        try:
            ActionChains(self.driver).move_to_element(el).pause(0.05).click().perform()
            logging.info(f"{name} clicked via Actions")
            return True
        except Exception:
            pass

        try:
            el.send_keys(Keys.ENTER)
            logging.info(f"{name} activated via ENTER")
            return True
        except Exception:
            pass

        try:
            self.driver.execute_script("""
                const el = arguments[0];
                const form = el.closest('form');
                if (form && form.requestSubmit) { form.requestSubmit(el); return true; }
                if (form) { form.submit(); return true; }
                return false;
            """, el)
            logging.info(f"{name} submitted via requestSubmit()")
            return True
        except Exception as e:
            logging.error(f"{name} all click paths failed: {e}")
            return False

    def _wait_url_or_text(self, target_texts, timeout=25):
        start = self.driver.current_url
        texpr = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        xp = (
            f"//button[@id='rs-checkout-continue-button-bottom' or @data-autom='continue-button-label']"
            f"[.//span//span[contains({texpr},'{target_texts[0]}')"
            + "".join([f" or contains({texpr},'{t}')" for t in target_texts[1:]]) + "]]"
        )
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (d.current_url != start) or len(d.find_elements(By.XPATH, xp)) > 0
            )
            return True
        except Exception:
            return False

    def _get_primary_button(self, texts=("continue to review","continue","place your order"), timeout=12):
        texpr = "translate(normalize-space(string(.)),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        xp = (
            f"//button[@id='rs-checkout-continue-button-bottom' or @data-autom='continue-button-label']"
            f"[.//span//span[contains({texpr},'{texts[0]}')"
            + "".join([f" or contains({texpr},'{t}')" for t in texts[1:]]) + "]]"
        )
        try:
            return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xp)))
        except Exception:
            try:
                return WebDriverWait(self.driver, 6).until(EC.element_to_be_clickable((By.ID, "rs-checkout-continue-button-bottom")))
            except Exception:
                return None        

    def fill_cvv_field(self, cvc_value, timeout=10):
        if self._stopped:
            return False
        
        logging.info("Filling CVC field")
        
        cvc_selectors = [
            "input[data-autom='security-code-input']",
            "input[id*='securityCode']",
            "input[name*='cvc']",
            "input[name*='cvv']",
            "input[autocomplete='cc-csc']",
            "input[aria-label*='security' i]",
            "input[aria-label*='cvc' i]",
            "input[aria-label*='cvv' i]",
            "input[placeholder*='cvc' i]",
            "input[placeholder*='cvv' i]",
            "input[placeholder*='security' i]",
            "input[id*='cvv']",
            "input[id*='cvc']"
        ]
        
        cvc_input = None
        for selector in cvc_selectors:
            try:
                cvc_input = WebDriverWait(self.driver, timeout//len(cvc_selectors)).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logging.info(f"Found CVC input using selector: {selector}")
                break
            except Exception:
                continue
        
        if not cvc_input:
            logging.error("CVC input field not found with any selector")
            return False
        
        cvc_str = str(cvc_value).strip()
        if not cvc_str or not cvc_str.isdigit():
            logging.error(f"Invalid CVC value: '{cvc_str}'")
            return False
        
        logging.info(f"Entering CVC: {'*' * len(cvc_str)} (length: {len(cvc_str)})")
        
        try:
            self._scroll_center(cvc_input)
            time.sleep(0.2)
            cvc_input.click()
            time.sleep(0.3)
        except Exception as e:
            logging.error(f"Error focusing CVC input: {e}")
        
        try:
            self.driver.execute_script("""
                const input = arguments[0];
                const value = arguments[1];
                
                input.focus();
                input.value = '';
                
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                
                setTimeout(() => {
                    input.value = value;
                    
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    input.dispatchEvent(new Event('blur', {bubbles: true}));
                }, 50);
            """, cvc_input, cvc_str)
            
            time.sleep(0.5)
            
            actual_value = cvc_input.get_attribute("value") or ""
            if actual_value.strip() == cvc_str:
                logging.info("CVC set successfully via JS")
                return True
            else:
                logging.error(f"JS method failed. Expected: '{cvc_str}', Got: '{actual_value}'")
                raise Exception("JS method verification failed")
                
        except Exception as e:
            logging.error(f"JS method failed: {e}, trying manual input...")
            
            try:
                cvc_input.click()
                time.sleep(0.1)
                
                clear_attempts = [
                    lambda: cvc_input.clear(),
                    lambda: cvc_input.send_keys(Keys.CONTROL + 'a', Keys.DELETE),
                    lambda: cvc_input.send_keys(Keys.COMMAND + 'a', Keys.DELETE),
                    lambda: self.driver.execute_script("arguments[0].value = '';", cvc_input)
                ]
                
                for clear_method in clear_attempts:
                    try:
                        clear_method()
                        time.sleep(0.1)
                        current_value = cvc_input.get_attribute("value") or ""
                        if not current_value.strip():
                            break
                    except Exception:
                        continue
                
                for i, char in enumerate(cvc_str):
                    try:
                        cvc_input.send_keys(char)
                        time.sleep(0.08)
                        
                        current_value = cvc_input.get_attribute("value") or ""
                        expected_so_far = cvc_str[:i+1]
                        
                        if not current_value.endswith(char):
                            logging.warning(f"Character '{char}' at position {i} may not have been entered correctly")
                            cvc_input.send_keys(char)
                            time.sleep(0.1)
                            
                    except Exception as char_error:
                        logging.error(f"Error typing character '{char}' at position {i}: {char_error}")
                        return False
                
                time.sleep(0.3)
                actual_value = cvc_input.get_attribute("value") or ""
                if actual_value.strip() != cvc_str:
                    logging.error(f"Manual CVC input verification failed. Expected: '{cvc_str}', Got: '{actual_value}'")
                    return False
                else:
                    logging.info("CVC entered successfully via manual input")
                    return True
                    
            except Exception as manual_error:
                logging.error(f"Manual CVC input method failed: {manual_error}")
                return False

    def fill_card_number_field(self, card_number, timeout=10):
        if self._stopped:
            return False
        
        logging.info("Filling card number field")
        
        card_digits = re.sub(r'\D+', '', str(card_number))
        
        if not card_digits or len(card_digits) < 13:
            logging.error(f"Invalid card number: length {len(card_digits)}")
            return False
        
        card_selectors = [
            "input[data-autom='card-number-input']",
            "input[id*='cardNumber']",
            "input[name*='cardNumber']",
            "input.form-textbox-number-input[autocomplete='cc-number']",
            "input[autocomplete='cc-number']",
            "input[aria-label*='card number' i]",
            "input[placeholder*='card number' i]"
        ]
        
        card_input = None
        for selector in card_selectors:
            try:
                card_input = WebDriverWait(self.driver, timeout//len(card_selectors)).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logging.info(f"Found card number input using selector: {selector}")
                break
            except Exception:
                continue
        
        if not card_input:
            logging.error("Card number input field not found")
            return False
        
        logging.info(f"Entering card number: {'*' * (len(card_digits) - 4)}{card_digits[-4:]}")
        
        try:
            self._scroll_center(card_input)
            time.sleep(0.2)
            card_input.click()
            time.sleep(0.3)
        except Exception as e:
            logging.error(f"Error focusing card input: {e}")
        
        try:
            card_input.clear()
            time.sleep(0.1)
            
            try:
                card_input.send_keys(Keys.CONTROL + 'a', Keys.DELETE)
            except:
                try:
                    card_input.send_keys(Keys.COMMAND + 'a', Keys.DELETE)
                except:
                    pass
            
            for i, char in enumerate(card_digits):
                try:
                    card_input.send_keys(char)
                    if (i + 1) % 4 == 0:
                        time.sleep(0.15)
                    else:
                        time.sleep(0.08)
                except Exception as char_error:
                    logging.error(f"Error typing card digit at position {i}: {char_error}")
                    return False
            
            time.sleep(0.5)
            actual_value = re.sub(r'\D+', '', card_input.get_attribute("value") or "")
            
            if actual_value != card_digits:
                logging.error(f"Card number verification failed. Expected length: {len(card_digits)}, Got length: {len(actual_value)}")
                return False
            else:
                logging.info("Card number entered successfully")
                return True
                
        except Exception as e:
            logging.error(f"Card number input failed: {e}")
            return False

    def handle_payment_form(self):
        if self._stopped:
            return False
        
        logging.info("Handling payment form")
        
        try:
            logging.info("Waiting for payment form to load")
            time.sleep(5)
            
            # Select credit card payment option with multiple methods
            logging.info("Selecting credit card payment")
            credit_selectors = [
                'input[id="checkout.billing.billingoptions.credit"]',
                'input[name="checkout.billing.billingoptions"][value="CREDIT"]',
                'input[type="radio"][value="CREDIT"]',
                'label[for="checkout.billing.billingoptions.credit"]'
            ]
            
            credit_clicked = False
            for selector in credit_selectors:
                try:
                    logging.info(f"Trying credit card selector: {selector}")
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
                            logging.info(f"Trying {method_name} on credit card option")
                            method()
                            time.sleep(2)
                            
                            # Check if it's selected
                            if element.is_selected() or element.get_attribute('checked'):
                                logging.info(f"Credit card option selected successfully using {method_name}")
                                credit_clicked = True
                                break
                        except Exception as e:
                            logging.info(f"{method_name} failed: {e}")
                            continue
                    
                    if credit_clicked:
                        break
                        
                except Exception as e:
                    logging.info(f"Credit selector {selector} failed: {e}")
                    continue
            
            if not credit_clicked:
                logging.info("Failed to select credit card option, trying label click")
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, 'label[for="checkout.billing.billingoptions.credit"]')
                    label.click()
                    logging.info("Credit card label clicked")
                    credit_clicked = True
                except:
                    logging.info("Label click also failed")
            
            if credit_clicked:
                logging.info("Waiting 10 seconds after credit card selection")
                time.sleep(10)
            else:
                logging.warning("Could not select credit card option, continuing anyway")
                time.sleep(3)
            
            # Get card data from user_data or config defaults
            card_number = getattr(self, 'card_data', {}).get('card_number', self.config.DEFAULT_VALUES['credit_card'])
            expiry_date = getattr(self, 'card_data', {}).get('expiry_date', self.config.DEFAULT_VALUES['expiry_date'])
            cvc = getattr(self, 'card_data', {}).get('cvc', self.config.DEFAULT_VALUES['cvc'])
            
            # Fill card number
            logging.info("Filling card number")
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
                    logging.info(f"Card number filled: {card_number[:4]}****{card_number[-4:]}")
                    break
                except Exception as e:
                    logging.info(f"Card number selector {selector} failed: {e}")
                    continue
            
            # Fill expiry date
            logging.info("Filling expiry date")
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
                    logging.info(f"Expiry date filled: {expiry_date}")
                    break
                except Exception as e:
                    logging.info(f"Expiry selector {selector} failed: {e}")
                    continue
            
            # Fill CVC
            logging.info("Filling CVC")
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
                    logging.info("CVC filled")
                    break
                except Exception as e:
                    logging.info(f"CVC selector {selector} failed: {e}")
                    continue
            
            # Scroll down 35% as requested
            logging.info("Scrolling down 35% of the page")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.35);")
            time.sleep(2)
            
            # Get billing data from card_data or fallback to user_data
            billing_info = getattr(self, 'card_data', {}).get('billing_info', {})
            first_name = billing_info.get('first_name', self.user_data['first_name'])
            last_name = billing_info.get('last_name', self.user_data['last_name'])
            street_address = billing_info.get('street_address', self.config.DEFAULT_VALUES['street_address'])
            postal_code = billing_info.get('postal_code', self.config.DEFAULT_VALUES['postal_code'])
            
            # Fill billing first name
            logging.info("Filling billing first name")
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
                    logging.info(f"Billing first name filled: {first_name}")
                    break
                except Exception as e:
                    logging.info(f"Billing first name selector {selector} failed: {e}")
                    continue
            
            # Fill billing last name
            logging.info("Filling billing last name")
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
                    logging.info(f"Billing last name filled: {last_name}")
                    break
                except Exception as e:
                    logging.info(f"Billing last name selector {selector} failed: {e}")
                    continue
            
            # Fill billing street address
            logging.info("Filling billing street address")
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
                    logging.info(f"Billing street filled: {street_address}")
                    break
                except Exception as e:
                    logging.info(f"Billing street selector {selector} failed: {e}")
                    continue
            
            # Fill billing postal code
            logging.info("Filling billing postal code")
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
                    logging.info(f"Billing postal code filled: {postal_code}")
                    break
                except Exception as e:
                    logging.info(f"Billing postal selector {selector} failed: {e}")
                    continue
            
            logging.info("Waiting 5 seconds")
            time.sleep(5)
            
            logging.info("Scrolling 100% and clicking continue")
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
                    logging.info("Continue button clicked successfully")
                    continue_clicked = True
                    time.sleep(3)
                    break
                except Exception as e:
                    logging.info(f"Continue selector {selector} failed: {e}")
                    continue
            
            if not continue_clicked:
                logging.error("Could not find continue button")
                return False
            
            return self.handle_final_order()
            
        except Exception as e:
            logging.error(f"Error in payment form handling: {e}")
            return False

    def handle_final_order(self):
        if self._stopped:
            return False
        
        logging.info("Final order page - scrolling 100% and clicking order")
        
        try:
            logging.info("Waiting for order page to load")
            time.sleep(5)
            
            # Scroll to 100% of the page
            logging.info("Scrolling to 100% of the page")
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
                    logging.info("Order button clicked successfully")
                    order_clicked = True
                    break
                except Exception as e:
                    logging.info(f"Order selector {selector} failed: {e}")
                    continue
            
            if not order_clicked:
                logging.error("Could not find order button")
                return False
            
            logging.info("Waiting 15 seconds before finishing")
            time.sleep(15)
            
            logging.info("ULTIMATE SUCCESS - COMPLETE AUTOMATION FINISHED!")
            logging.info("All automation steps completed successfully:")
            logging.info("1. No Coverage selected")
            logging.info("2. 2 iPhones added to bag")
            logging.info("3. Checkout process completed")
            logging.info("4. Guest login completed")
            logging.info("5. Pickup option selected")
            logging.info("6. Zip code entered and store selected")
            logging.info("7. Time slot selected")
            logging.info("8. Contact forms filled")
            logging.info("9. Payment form filled")
            logging.info("10. Continue clicked")
            logging.info("11. Order placed")
            logging.info("AUTOMATION CYCLE COMPLETE - READY TO RESTART")
            
            return True
            
        except Exception as e:
            logging.error(f"Error in final order handling: {e}")
            return False

    def run_purchase_flow(self):
        if self._stopped:
            return False
        logging.info(f"Starting purchase flow for iPhone {self.purchase_count + 1}")
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
        except Exception:
            pass
        time.sleep(0.6)
        if not self.click_applecare_no_coverage():
            return False
        if not self.add_to_bag():
            return False
        return self.handle_bag_page()

    def _run_once(self):
        try:
            logging.info("Starting Apple automation")
            logging.info(f"Bright Data session: {self.proxy_session}")
            logging.info(f"Target: {self.max_purchases} iPhones")
            logging.info(f"User: {self.user_data['first_name']} {self.user_data['last_name']} - {self.user_data['email']}")
            logging.info(f"ZIP: {self.user_data['zip_code']}")

            if not self.setup_driver():
                return False
            if self._stopped:
                return False

            logging.info("Opening product page")
            self.driver.set_page_load_timeout(max(20, getattr(self.config, "PAGE_LOAD_TIMEOUT", 20)))
            self.driver.get(self.config.PRODUCT_URL)
            WebDriverWait(self.driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            logging.info("Page loaded")

            self.saved_link = self.driver.current_url

            ok = self.run_purchase_flow()
            if ok:
                logging.info("Flow completed successfully")
            else:
                logging.error("Flow failed")
            return ok
        except (TimeoutException, WebDriverException) as e:
            logging.error(f"WebDriver error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            traceback.print_exc()
            return False
        finally:
            try:
                if self.driver and not bool(getattr(self.config, "KEEP_BROWSER_OPEN", False)):
                    self.driver.quit()
            except Exception:
                pass

    def _set_new_session_for_next_run(self):
        if not self.use_proxy:
            return
        import secrets
        os.environ["OXY_SESSID"] = secrets.token_hex(6)
        self.proxy_session = os.environ["OXY_SESSID"]

    def run(self):
        runs = 0
        while True:
            runs += 1
            logging.info(f"RUN #{runs}")
            ok = self._run_once()

            if not self.auto_restart:
                return ok
            if self.max_runs and runs >= self.max_runs:
                logging.info(f"Reached max runs ({self.max_runs}). Stopping.")
                return ok

            self._set_new_session_for_next_run()
            logging.info(f"Next run will use new proxy_session={self.proxy_session}")
            time.sleep(1.5)


if __name__ == "__main__":
    bot = AppleAutomation()
    bot.run()