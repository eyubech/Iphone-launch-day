# config.py
import os
import time

class Config:
    # ---- App/runtime defaults your code expects ----
    AUTO_RESTART = False            # set True if you want the supervisor loop
    MAX_RUNS = 1
    PAGE_LOAD_TIMEOUT = 25
    BROWSER_OPTIONS = [
        # add "--headless=new" if you want headless
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1400,1000",
        "--lang=en-US,en;q=0.9",
        "--disable-background-networking",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--disable-features=NetworkService,NetworkServiceInProcess",
    ]
    SECURE_DIRECT_PROXY = True

    # A safe default product page (change as needed)
    PRODUCT_URL = os.getenv(
        "PRODUCT_URL",
        "https://www.apple.com/shop/buy-iphone/iphone-17-pro/6.3-inch-display-256gb-deep-blue-unlocked",
    )

    # Data used by the form fillers when nothing else is provided
    DEFAULT_VALUES = {
        "street_address": "1 Infinite Loop",
        "postal_code": "95014",
        "credit_card": "4111111111111111",
        "expiry_date": "12/27",
        "cvc": "123",
        "first_name": "test",
        "last_name": "test",
        "email": "test@example.com",
        "phone": "3055551234",
        "zip_code": "33165",
    }

    # ---- Oxylabs <-> “Bright Data” field shim so existing code keeps working ----
    # Toggle with USE_PROXY=1
    BRIGHT_DATA_ENABLE = bool(int(os.getenv("USE_PROXY", "0")))

    # Base Oxylabs creds/host. You can override via env if needed.
    OXY_USERNAME_BASE = os.getenv("OXY_USERNAME", "customer-garrajemobile_uKxOe")
    OXY_PASSWORD     = os.getenv("OXY_PASSWORD", "ev3FJequ_m7pHt7")
    OXY_HOST         = os.getenv("OXY_HOST", "us-pr.oxylabs.io")
    OXY_PORT         = int(os.getenv("OXY_PORT", "10000"))
    OXY_CC           = os.getenv("OXY_CC", "us")  # keep it simple: country only at first

    # Some parts of the app check this attribute; provide a harmless value
    BRIGHT_DATA_ZONE_ID = "oxylabs"

    # Map to the names your Selenium code already reads
    @property
    def BRIGHT_DATA_USERNAME(self) -> str:
        # rotating sticky session id
        sid = str(int(time.time() * 1000) % 1_000_000)
        return f"{self.OXY_USERNAME_BASE}-cc-{self.OXY_CC}-session-{sid}"
        # If your plan includes city/state targeting, you can later extend:
        # return f"{self.OXY_USERNAME_BASE}-cc-us-state-fl-city-miami-session-{sid}"

    @property
    def BRIGHT_DATA_PASSWORD(self) -> str:
        return self.OXY_PASSWORD

    @property
    def BRIGHT_DATA_ENDPOINT(self) -> str:
        return self.OXY_HOST

    @property
    def BRIGHT_DATA_PORT(self) -> int:
        return self.OXY_PORT
