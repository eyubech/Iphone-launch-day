"""
Configuration file for Apple iPhone automation script
"""

class Config:
    # Browser settings
    BROWSER_OPTIONS = [
        "--disable-blink-features=AutomationControlled",
        "--disable-automation"
    ]
    
    # Timeouts (in seconds)
    PAGE_LOAD_TIMEOUT = 20
    ELEMENT_TIMEOUT = 10
    SHORT_WAIT = 1
    MEDIUM_WAIT = 2
    LONG_WAIT = 5
    FINAL_WAIT = 50
    
    # Scroll settings
    SCROLL_PERCENTAGE = 0.22
    
    # Default values (can be overridden by user input)
    DEFAULT_VALUES = {
        'zip_code': '33165',
        'first_name': 'test',
        'last_name': 'test',
        'email': 'test@gmail.com',
        'phone': '3422342342',
        'street_address': 'test test test test test test test test',
        'postal_code': '32003',
        'credit_card': '4242424242424242',
        'expiry_date': '04/26',
        'cvc': '123'
    }
    
    # CSS Selectors
    SELECTORS = {
        'applecare_no': "[class*='applecare'][class*='no'], [data-autom*='noapple']",
        'pickup_button': "button.rf-pickup-quote-overlay-trigger",
        'zip_input': "input[name='search'][type='text']",
        'store_elements': "li.rf-productlocator-storeoption",
        'store_name': ".form-selector-title",
        'store_location': ".form-label-small",
        'store_radio': "input[type='radio']",
        
        # Continue buttons
        'continue_pickup': [
            "button[data-autom='continuePickUp']",
            "button[data-autom*='continue']",
            ".button.button-block.rf-productlocator-selectstore",
            "button.button.button-block",
            ".rf-productlocator-selectstore",
            "button[type='button'][class*='button-block']"
        ],
        
        # Add to bag buttons
        'add_to_bag': [
            "button[data-autom='add-to-cart']",
            "button[name='add-to-cart']",
            ".button[data-autom='add-to-cart']",
            "button[class*='add-to-cart']",
            ".as-purchaseinfo-button button",
            "form button[type='submit']"
        ],
        
        # Review bag buttons
        'review_bag': [
            "button[data-autom='proceed']",
            "button[name='proceed']",
            "button[value='proceed']",
            ".button.button-block[data-autom='proceed']",
            "form button[type='submit']",
            "button[class*='button-block']"
        ],
        
        # Checkout buttons
        'checkout': [
            "button[id='shoppingCart.actions.navCheckoutOtherPayments']",
            "button.button.button-block.rs-bag-checkout-otheroptions",
            ".rs-bag-checkoutbutton button",
            "button[class*='checkout']",
            ".rs-bag-checkoutbuttons-wrapper button",
            "button[type='button'][class*='button-block']"
        ],
        
        # Guest checkout buttons
        'guest_checkout': [
            "button[data-autom='guest-checkout-btn']",
            "button[id='signin.guestLogin.guestLogin']",
            ".form-button[data-autom='guest-checkout-btn']",
            "button[class*='guest-checkout']",
            ".rs-sign-in-sidebar button",
            "button[type='button'][class*='form-button']"
        ],
        
        # Pickup time dropdown
        'pickup_time_dropdown': [
            "select[id='checkout.fulfillment.pickupTab.pickup.timeSlot.dateTimeSlots.timeSlotValue']",
            "select[data-autom='pickup-availablewindow-dropdown']",
            ".form-dropdown-selector select",
            "select[class*='form-dropdown']",
            ".rs-pickup-slottitle select"
        ],
        
        # Final continue buttons
        'final_continue': [
            "button[id='rs-checkout-continue-button-bottom']",
            "button[data-autom='fulfillment-continue-button']",
            ".rs-checkout-action button",
            "button.form-button",
            "button[type='button'][class*='form-button']",
            ".rs-checkout-action-button-wrapper button"
        ],
        
        # Third party pickup
        'third_party_pickup': [
            "button[data-autom='thirdPartyPickup']",
            "input[data-autom='thirdPartyPickup']",
            ".rc-segmented-control-item button[data-autom='thirdPartyPickup']",
            "button[role='radio'][data-autom='thirdPartyPickup']",
            ".rc-segmented-control-item[data-autom='thirdPartyPickup']"
        ],
        
        # Form fields
        'first_name': [
            "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.firstName']",
            "input[name='firstName']",
            "input[data-autom='form-field-firstName']"
        ],
        
        'last_name': [
            "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.lastName']",
            "input[name='lastName']",
            "input[data-autom='form-field-lastName']"
        ],
        
        'email': [
            "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.emailAddress']",
            "input[name='emailAddress']",
            "input[type='email']",
            "input[data-autom='form-field-emailAddress']"
        ],
        
        'phone': [
            "input[id='checkout.pickupContact.selfPickupContact.selfContact.address.fullDaytimePhone']",
            "input[name='fullDaytimePhone']",
            "input[type='tel']",
            "input[data-autom='form-field-fullDaytimePhone']"
        ],
        
        # Billing fields
        'billing_email': [
            "input[id='checkout.pickupContact.thirdPartyPickupContact.billingContact.address.emailAddress']",
            "input[name='emailAddress'][type='email']",
            "input[data-autom='form-field-emailAddress']"
        ],
        
        'billing_phone': [
            "input[id='checkout.pickupContact.thirdPartyPickupContact.billingContact.address.fullDaytimePhone']",
            "input[name='fullDaytimePhone'][type='tel']",
            "input[data-autom='form-field-fullDaytimePhone']"
        ],
        
        # Payment fields
        'credit_payment': "input#checkout\\.billing\\.billingoptions\\.credit",
        'card_number': "input[id*='cardNumber']",
        'expiry': "input[id*='expiration']",
        'cvc': "input[id*='securityCode']",
        
        # Billing address fields
        'billing_first_name': "input[id='checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.firstName']",
        'billing_last_name': "input[id='checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.lastName']",
        'billing_street': "input[id='checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.street']",
        'billing_postal_code': "input[id='checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.zipLookup.postalCode']",
        
        # Checkboxes
        'notification_checkbox': [
            "input[id='checkout.pickupContact.thirdPartyPickupContact.thirdPartyContact.acceptTextNotification']",
            "input[type='checkbox']",
            ".form-checkbox input"
        ],
        
        # Continue to payment buttons
        'continue_payment': [
            "button[data-autom='continue-button-label']",
            "button[id='rs-checkout-continue-button-bottom']",
            ".rs-checkout-action button",
            "button[class*='form-button']"
        ]
    }
    
    # Product URL
    PRODUCT_URL = "https://www.apple.com/shop/buy-iphone/iphone-16-pro/6.3-inch-display-128gb-desert-titanium-unlocked"