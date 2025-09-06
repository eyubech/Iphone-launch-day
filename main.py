"""
User Interface for Apple iPhone automation script
"""

from apple_automation import AppleAutomation
from config import Config


def get_user_input():
    """Get user input for automation parameters"""
    print("=" * 60)
    print("APPLE IPHONE AUTOMATION SCRIPT")
    print("=" * 60)
    print()
    
    print("Choose an option:")
    print("1. Use default test values (recommended for testing)")
    print("2. Enter custom values")
    print("3. View default values before deciding")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\nUsing default test values...")
            return Config.DEFAULT_VALUES
        
        elif choice == "2":
            return get_custom_values()
        
        elif choice == "3":
            show_default_values()
            print("\nChoose an option:")
            print("1. Use these default values")
            print("2. Enter custom values")
            
            sub_choice = input("Enter your choice (1-2): ").strip()
            if sub_choice == "1":
                return Config.DEFAULT_VALUES
            elif sub_choice == "2":
                return get_custom_values()
            else:
                print("Invalid choice. Please try again.")
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def show_default_values():
    """Display the default values"""
    print("\n" + "=" * 40)
    print("DEFAULT TEST VALUES:")
    print("=" * 40)
    
    config = Config()
    for key, value in config.DEFAULT_VALUES.items():
        formatted_key = key.replace('_', ' ').title()
        print(f"{formatted_key}: {value}")
    
    print("=" * 40)


def get_custom_values():
    """Get custom values from user input"""
    print("\n" + "=" * 40)
    print("ENTER CUSTOM VALUES:")
    print("=" * 40)
    print("Enter your custom values (press Enter for default value shown in brackets):")
    print()
    
    config = Config()
    user_data = {}
    
    # Define input prompts with validation
    input_fields = [
        ('zip_code', 'Zip Code', str, None),
        ('first_name', 'First Name', str, None),
        ('last_name', 'Last Name', str, None),
        ('email', 'Email Address', str, validate_email),
        ('phone', 'Phone Number', str, validate_phone),
        ('street_address', 'Street Address', str, None),
        ('postal_code', 'Postal Code', str, None),
        ('credit_card', 'Credit Card Number', str, validate_credit_card),
        ('expiry_date', 'Expiry Date (MM/YY)', str, validate_expiry),
        ('cvc', 'CVC Code', str, validate_cvc)
    ]
    
    for key, prompt, data_type, validator in input_fields:
        default_value = config.DEFAULT_VALUES[key]
        
        while True:
            user_input = input(f"{prompt} [{default_value}]: ").strip()
            
            # Use default if empty
            if not user_input:
                user_data[key] = default_value
                break
            
            # Validate input if validator provided
            if validator:
                is_valid, error_msg = validator(user_input)
                if not is_valid:
                    print(f"Error: {error_msg}")
                    continue
            
            user_data[key] = user_input
            break
    
    return user_data


def validate_email(email):
    """Basic email validation"""
    if '@' in email and '.' in email.split('@')[1]:
        return True, ""
    return False, "Invalid email format. Please enter a valid email address."


def validate_phone(phone):
    """Basic phone validation"""
    # Remove common formatting characters
    clean_phone = ''.join(c for c in phone if c.isdigit())
    if len(clean_phone) >= 10:
        return True, ""
    return False, "Phone number must contain at least 10 digits."


def validate_credit_card(card_number):
    """Basic credit card validation"""
    # Remove spaces and dashes
    clean_card = ''.join(c for c in card_number if c.isdigit())
    if len(clean_card) >= 13 and len(clean_card) <= 19:
        return True, ""
    return False, "Credit card number must be between 13-19 digits."


def validate_expiry(expiry):
    """Basic expiry date validation"""
    if len(expiry) == 5 and expiry[2] == '/' and expiry[:2].isdigit() and expiry[3:].isdigit():
        month = int(expiry[:2])
        if 1 <= month <= 12:
            return True, ""
    return False, "Expiry date must be in MM/YY format (e.g., 04/26)."


def validate_cvc(cvc):
    """Basic CVC validation"""
    if cvc.isdigit() and len(cvc) >= 3 and len(cvc) <= 4:
        return True, ""
    return False, "CVC must be 3-4 digits."


def confirm_values(user_data):
    """Display values for user confirmation"""
    print("\n" + "=" * 50)
    print("CONFIRMATION - PLEASE REVIEW YOUR VALUES:")
    print("=" * 50)
    
    for key, value in user_data.items():
        formatted_key = key.replace('_', ' ').title()
        # Mask sensitive information
        if key == 'credit_card':
            masked_value = '*' * (len(value) - 4) + value[-4:]
            print(f"{formatted_key}: {masked_value}")
        elif key == 'cvc':
            print(f"{formatted_key}: ***")
        else:
            print(f"{formatted_key}: {value}")
    
    print("=" * 50)
    
    while True:
        confirm = input("\nProceed with these values? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return True
        elif confirm in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def main():
    """Main function to run the automation"""
    try:
        # Get user input
        user_data = get_user_input()
        
        # Confirm values if custom input was provided
        if user_data != Config.DEFAULT_VALUES:
            if not confirm_values(user_data):
                print("Automation cancelled by user.")
                return
        
        print("\n" + "=" * 60)
        print("STARTING AUTOMATION...")
        print("=" * 60)
        print()
        print("The automation will now:")
        print("1. Open Apple's website")
        print("2. Navigate through the iPhone purchase process")
        print("3. Check store availability in your area")
        print("4. Fill out forms with your provided information")
        print("5. Proceed to the payment page")
        print()
        print("Note: The browser will remain open for 50 seconds at the end")
        print("so you can see the final results.")
        print()
        
        input("Press Enter to start the automation...")
        
        # Run automation
        automation = AppleAutomation(user_data)
        success = automation.run_automation()
        
        if success:
            print("\n" + "=" * 60)
            print("AUTOMATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("All steps were executed. Check the browser for final results.")
        else:
            print("\n" + "=" * 60)
            print("AUTOMATION ENCOUNTERED ISSUES")
            print("=" * 60)
            print("Some steps may not have completed successfully.")
            print("Check the console output above for details.")
    
    except KeyboardInterrupt:
        print("\n\nAutomation interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your input values and try again.")


if __name__ == "__main__":
    main()