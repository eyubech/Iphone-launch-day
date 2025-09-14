// ==UserScript==
// @name         iPhone Order Bot - Apple Secure
// @namespace    http://tampermonkey.net/
// @version      2.4
// @description  Automatically order iPhone with no coverage option across all Apple pages
// @author       You
// @match        *://www.apple.com/*
// @match        *://*.apple.com/*
// @match        *://store.apple.com/*
// @match        *://*.store.apple.com/*
// @match        *://secure*.store.apple.com/*
// @match        *://secure7.store.apple.com/*
// @run-at       document-end
// @grant        none
// ==/UserScript==
(function () {
    'use strict';

    const FirstName = "test";
    const LastName = "test";
    const StreetAddress = "2934 NW 72nd Ave"
    const Email = "test@example.com";
    const Phone = "1234567890";
    const PostalCode = "33122";
    const CardNumber = "4111111111111111";
    const ExpirationDate = "0426";
    const SecurityCode = "123";

    let clickedButtons = {
        appleCare: false,
        addToCart: false,
        proceed: false,
        otherPayments: false,
        guestLogin: false,
        continueButton: false,
        billingCredit: false,
        finalButton: false,
        shippingCheckbox: false
    };

    let formFilled = false;
    let creditCardFilled = false;

    const scrollDown = () => {
        const y = document.body.scrollHeight * 0.25;
        window.scrollTo({ top: y, behavior: 'smooth' });
    };

    const scrollToBottom = () => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    };

    const waitForAppleCare = () => {
        if (clickedButtons.appleCare) return;
        const radios = document.querySelectorAll('input[name="applecare-options"]');
        if (radios.length >= 3) {
            radios[2].click();
            clickedButtons.appleCare = true;
            waitForAddToCart();
        } else {
            setTimeout(waitForAppleCare, 100);
        }
    };

    const waitForAddToCart = () => {
        if (clickedButtons.addToCart) return;
        const addBtn = document.querySelector('[name="add-to-cart"]');
        if (addBtn) {
            addBtn.click();
            clickedButtons.addToCart = true;
        } else {
            setTimeout(waitForAddToCart, 100);
        }
    };

    const waitForProceed = () => {
        if (clickedButtons.proceed) return;
        const proceedBtn = document.querySelector('[name="proceed"]');
        if (proceedBtn) {
            proceedBtn.click();
            clickedButtons.proceed = true;
        } else {
            setTimeout(waitForProceed, 100);
        }
    };

    const waitForOtherPayments = () => {
        if (clickedButtons.otherPayments) return;
        const otherBtn = document.querySelector('#shoppingCart\\.actions\\.navCheckoutOtherPayments');
        if (otherBtn) {
            otherBtn.click();
            clickedButtons.otherPayments = true;
        } else {
            setTimeout(waitForOtherPayments, 100);
        }
    };

    const waitForGuestLogin = () => {
        if (clickedButtons.guestLogin) return;
        const guestBtn = document.querySelector('#signIn\\.guestLogin\\.guestLogin');
        if (guestBtn) {
            guestBtn.click();
            clickedButtons.guestLogin = true;
        } else {
            setTimeout(waitForGuestLogin, 100);
        }
    };

    const checkDeliveryDate = () => {
        const deliveryElements = document.querySelectorAll('.rs-fulfillment-sectiontitle span');
        for (let element of deliveryElements) {
            const text = element.textContent;
            if (text.includes('Delivers') && text.includes('Sep')) {
                const match = text.match(/Sep\s+(\d{1,2})/);
                if (match) {
                    const day = parseInt(match[1]);
                    if (day !== 19) {
                        return false;
                    }
                }
            }
        }
        return true;
    };

    const waitForContinueButton = () => {
        if (clickedButtons.continueButton) return;
        const continueBtn = document.querySelector('#rs-checkout-continue-button-bottom');
        if (continueBtn) {
            if (!checkDeliveryDate()) {
                return;
            }
            scrollToBottom();
            setTimeout(() => {
                continueBtn.click();
                clickedButtons.continueButton = true;
                setTimeout(() => {
                    checkAllPages();
                }, 2000);
            }, 300);
        } else {
            setTimeout(waitForContinueButton, 100);
        }
    };

    const waitForBillingCredit = () => {
        if (clickedButtons.billingCredit) return;
        const billingCreditBtn = document.getElementById('checkout.billing.billingoptions.credit');
        if (billingCreditBtn) {
            billingCreditBtn.click();
            clickedButtons.billingCredit = true;
            setTimeout(() => {
                checkAllPages();
            }, 5000);
        } else {
            setTimeout(waitForBillingCredit, 200);
        }
    };

    const setInputValue = (input, value) => {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeInputValueSetter.call(input, value);

        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.dispatchEvent(new Event('blur', { bubbles: true }));
    };

    const fillAllFields = () => {
        if (formFilled) return;

        const firstName = document.getElementById('checkout.shipping.addressSelector.newAddress.address.firstName');
        const lastName = document.getElementById('checkout.shipping.addressSelector.newAddress.address.lastName');
        const street = document.getElementById('checkout.shipping.addressSelector.newAddress.address.street');
        const email = document.getElementById('checkout.shipping.addressContactEmail.address.emailAddress');
        const phone = document.getElementById('checkout.shipping.addressContactPhone.address.fullDaytimePhone');
        const postalCodeInput = document.getElementById('checkout.shipping.addressSelector.newAddress.address.zipLookup.postalCode');

        if (firstName && lastName && street && email && phone && postalCodeInput) {
            formFilled = true;

            setInputValue(firstName, FirstName);
            setTimeout(() => {
                setInputValue(lastName, LastName);
                setTimeout(() => {
                    setInputValue(street, StreetAddress);
                    setTimeout(() => {
                        setInputValue(postalCodeInput, PostalCode);
                        setTimeout(() => {
                            setInputValue(email, Email);
                            setTimeout(() => {
                                setInputValue(phone, Phone);
                                setTimeout(() => {
                                    const continueBtn = document.getElementById('rs-checkout-continue-button-bottom');
                                    if (continueBtn) {
                                        scrollToBottom();
                                        setTimeout(() => {
                                            continueBtn.click();
                                            setTimeout(() => {
                                                checkAllPages();
                                            }, 2000);
                                        }, 500);
                                    }
                                }, 200);
                            }, 200);
                        }, 200);
                    }, 200);
                }, 200);
            }, 200);
        } else {
            setTimeout(fillAllFields, 300);
        }
    };

    const waitForShippingCheckbox = () => {
        if (clickedButtons.shippingCheckbox) return;
        const shippingCheckbox = document.getElementById(':r1f:');
        if (shippingCheckbox) {
            shippingCheckbox.click();
            clickedButtons.shippingCheckbox = true;
            setTimeout(() => {
                const continueBtn = document.getElementById('rs-checkout-continue-button-bottom');
                if (continueBtn) {
                    scrollToBottom();
                    setTimeout(() => {
                        continueBtn.click();
                        setTimeout(() => {
                            checkAllPages();
                        }, 2000);
                    }, 500);
                }
            }, 300);
        } else {
            setTimeout(waitForShippingCheckbox, 200);
        }
    };

    const fillCreditCardFields = () => {
        if (creditCardFilled) return;

        const cardNumber = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.cardNumber');
        const expiration = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.expiration');
        const securityCode = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.securityCode');

        if (cardNumber && expiration && securityCode) {
            creditCardFilled = true;

            setInputValue(cardNumber, CardNumber);
            setTimeout(() => {
                setInputValue(expiration, ExpirationDate);
                setTimeout(() => {
                    setInputValue(securityCode, SecurityCode);
                    setTimeout(() => {
                        clickShippingCheckbox();
                    }, 1000);
                }, 300);
            }, 300);
        } else {
            setTimeout(fillCreditCardFields, 1000);
        }
    };

    const clickShippingCheckbox = () => {
        const shippingCheckbox = document.getElementById(':r1f:');
        if (shippingCheckbox) {
            shippingCheckbox.click();
            setTimeout(() => {
                fillBillingAddressFields();
            }, 10000);
        } else {
            setTimeout(clickShippingCheckbox, 200);
        }
    };

    const fillBillingAddressFields = () => {
        const billingFirstName = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.firstName');
        const billingLastName = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.lastName');
        const billingStreet = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.street');
        const billingPostalCode = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.billingAddress.address.zipLookup.postalCode');

        if (billingFirstName && billingLastName && billingStreet && billingPostalCode) {
            setInputValue(billingFirstName, FirstName);
            setTimeout(() => {
                setInputValue(billingLastName, LastName);
                setTimeout(() => {
                    setInputValue(billingStreet, StreetAddress);
                    setTimeout(() => {
                        setInputValue(billingPostalCode, PostalCode);
                        scrollToBottom();
                        setTimeout(() => {
                            clickFirstContinue();
                        }, 10000);
                    }, 300);
                }, 300);
            }, 300);
        } else {
            setTimeout(fillBillingAddressFields, 1000);
        }
    };

    const clickFirstContinue = () => {
        const continueBtn = document.getElementById('rs-checkout-continue-button-bottom');
        if (continueBtn) {
            continueBtn.click();
            setTimeout(() => {
                scrollToBottomAndContinue();
            }, 20000);
        } else {
            setTimeout(clickFirstContinue, 500);
        }
    };

    const scrollToBottomAndContinue = () => {
        scrollToBottom();
        setTimeout(() => {
            const finalContinueBtn = document.getElementById('rs-checkout-continue-button-bottom');
            if (finalContinueBtn) {
                finalContinueBtn.click();
            } else {
                setTimeout(scrollToBottomAndContinue, 500);
            }
        }, 1000);
    };

    const checkAllPages = () => {
        if (creditCardFilled) return; // Stop if credit card is already filled

        if (document.querySelector('input[name="applecare-options"]') && !clickedButtons.appleCare) {
            scrollDown();
            setTimeout(waitForAppleCare, 200);
            return;
        }

        if (document.querySelector('[name="proceed"]') && !clickedButtons.proceed) {
            setTimeout(waitForProceed, 200);
            return;
        }

        if (document.querySelector('#shoppingCart\\.actions\\.navCheckoutOtherPayments') && !clickedButtons.otherPayments) {
            setTimeout(waitForOtherPayments, 200);
            return;
        }

        if (document.querySelector('#signIn\\.guestLogin\\.guestLogin') && !clickedButtons.guestLogin) {
            setTimeout(waitForGuestLogin, 200);
            return;
        }

        if (document.querySelector('#rs-checkout-continue-button-bottom') && !clickedButtons.continueButton) {
            setTimeout(waitForContinueButton, 200);
            return;
        }

        if (document.getElementById('checkout.shipping.addressSelector.newAddress.address.firstName') && !formFilled) {
            setTimeout(fillAllFields, 200);
            return;
        }

        if (document.getElementById('checkout.billing.billingoptions.credit') && !clickedButtons.billingCredit) {
            setTimeout(waitForBillingCredit, 200);
            return;
        }

        if (clickedButtons.billingCredit && !creditCardFilled) {
            const cardNumber = document.getElementById('checkout.billing.billingOptions.selectedBillingOptions.creditCard.cardInputs.cardInput-0.cardNumber');
            if (cardNumber) {
                setTimeout(fillCreditCardFields, 200);
                return;
            }
        }

        if (document.getElementById(':r1f:') && !clickedButtons.shippingCheckbox) {
            setTimeout(waitForShippingCheckbox, 200);
            return;
        }

        setTimeout(checkAllPages, 2000);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAllPages);
    } else {
        checkAllPages();
    }

    window.addEventListener('load', checkAllPages);
    setTimeout(checkAllPages, 1000);
    setTimeout(checkAllPages, 3000);
})();