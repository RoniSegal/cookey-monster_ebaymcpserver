import base64
import json
import os
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Function to generate an OAuth2 access token
def get_access_token(CLIENT_ID, CLIENT_SECRET):
    TOKEN_FILE = "nameOfTokenToStoreUrEbayToken.json"
    # Check if the token already exists and is valid
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            token_data = json.load(file)
            expiration_time = datetime.fromisoformat(token_data["expires_at"])
            if expiration_time > datetime.now():
                return token_data["access_token"]

    # If the token is expired or doesn't exist, generate a new one
    auth = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_auth}",
    }

    API_SCOPE = "https://api.ebay.com/oauth/api_scope"           # scope aka what it how much of ebay resources it has access
    OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"  # send post request to this link to get token

    data = {
        "grant_type": "client_credentials",
        "scope": API_SCOPE,
    }

    response = requests.post(OAUTH_URL, headers=headers, data=data)
    if response.status_code == 200:
        token_response = response.json()
        access_token = token_response["access_token"]
        expires_in = token_response["expires_in"]

        # Store the token and expiration time locally
        token_data = {
            "access_token": access_token,
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
        }
        with open("ebay_token.json", "w") as file:
            json.dump(token_data, file)

        return access_token
    else:
        raise Exception(f"Error generating token: {response.status_code} {response.text}")

# Function to make an authenticated eBay API request
def make_ebay_api_request(access_token, query=None, ammount=int, upc=None):
    access_token = access_token

    # Define the eBay Browse API endpoint
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    # Build params based on whether query or UPC is provided
    params = {
        "limit": ammount,
    }
    
    # Build filter string
    filters = ["buyingOptions:{FIXED_PRICE}"]
    
    # If UPC is provided, use gtin filter
    if upc:
        filters.append(f"gtin:{upc}")
    
    params["filter"] = ",".join(filters)
    
    # Add query if provided (can be used with or without UPC)
    if query:
        params["q"] = query

    response = requests.get(url, headers=headers, params=params)
    ebay_search_results = []

    if response.status_code == 200:
        results = response.json().get("itemSummaries", [])
        if not results:
            return "No listings found"

        # Format and display the results
        for item in results:
            title = item.get("title", "N/A")
            price =  item.get("price", {}).get("value")
            currency = item.get("price", {}).get("currency", "N/A")
            end_date = item.get("itemEndDate", "N/A")
            
            # Parse and format the listing end time if available
            if end_date != "N/A":
                end_time = datetime.fromisoformat(end_date[:-1]).strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_time = "N/A"

            ebay_search_results.append([title, price, currency, end_date, item.get('itemWebUrl', 'N/A')])

        return ebay_search_results
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Function to send a message to an eBay seller using browser automation
def send_message_to_seller(ebay_username, ebay_password, item_id, subject, message_body):
    """
    Send a message to an eBay seller about a specific item using browser automation.
    This creative solution bypasses API limitations by automating the "Contact Seller" feature.
    
    IMPORTANT: This requires your eBay login credentials and uses browser automation
    to simulate clicking the "Contact Seller" button on the item page.
    
    Args:
        ebay_username: Your eBay username/email for login
        ebay_password: Your eBay password for login
        item_id: The eBay item ID
        subject: Message subject (topic selection)
        message_body: Message content
    
    Returns:
        Dictionary with success status and message
    """
    driver = None
    
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Navigate to the item page
        item_url = f"https://www.ebay.com/itm/{item_id}"
        driver.get(item_url)
        
        wait = WebDriverWait(driver, 10)
        
        # Check if we need to login first
        # Look for "Contact seller" link - it might require login
        try:
            # Try to find the contact seller link/button
            contact_selectors = [
                "//a[contains(text(), 'Contact seller')]",
                "//a[contains(text(), 'Ask a question')]",
                "//button[contains(text(), 'Contact seller')]",
                "//a[@class='vim d-vi-acc-dspl-btn-cvr-all']"
            ]
            
            contact_button = None
            for selector in contact_selectors:
                try:
                    contact_button = driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not contact_button:
                # If we can't find the button, we might need to login
                # Navigate to eBay sign in page
                driver.get("https://signin.ebay.com/")
                
                # Wait for and fill in username
                username_field = wait.until(
                    EC.presence_of_element_located((By.ID, "userid"))
                )
                username_field.send_keys(ebay_username)
                
                # Click continue button
                continue_button = driver.find_element(By.ID, "signin-continue-btn")
                continue_button.click()
                
                time.sleep(2)
                
                # Wait for and fill in password
                password_field = wait.until(
                    EC.presence_of_element_located((By.ID, "pass"))
                )
                password_field.send_keys(ebay_password)
                
                # Click sign in button
                signin_button = driver.find_element(By.ID, "sgnBt")
                signin_button.click()
                
                time.sleep(3)
                
                # Navigate back to item page after login
                driver.get(item_url)
                time.sleep(2)
            
            # Now try to find and click the contact seller button
            contact_button = None
            for selector in contact_selectors:
                try:
                    contact_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not contact_button:
                return {
                    "success": False,
                    "message": "Could not find 'Contact Seller' button on item page. The seller may not allow messages or the item may not exist."
                }
            
            # Click the contact seller button
            driver.execute_script("arguments[0].click();", contact_button)
            time.sleep(2)
            
            # Handle the contact form (varies by eBay's current interface)
            # Try to find the message/question field
            message_selectors = [
                "//textarea[@name='comments']",
                "//textarea[@id='comments']",
                "//textarea[contains(@class, 'comments')]",
                "//textarea[@placeholder='Type your question']",
                "//textarea"
            ]
            
            message_field = None
            for selector in message_selectors:
                try:
                    message_field = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not message_field:
                return {
                    "success": False,
                    "message": "Could not find message field in contact form. eBay's interface may have changed."
                }
            
            # Fill in the message
            full_message = f"{subject}\n\n{message_body}"
            message_field.clear()
            message_field.send_keys(full_message)
            
            time.sleep(1)
            
            # Find and click the send/submit button
            send_selectors = [
                "//button[contains(text(), 'Send')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//button[contains(text(), 'Submit')]"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not send_button:
                return {
                    "success": False,
                    "message": "Could not find send button. Message was typed but not sent."
                }
            
            # Click send
            driver.execute_script("arguments[0].click();", send_button)
            time.sleep(3)
            
            # Check for success confirmation
            # eBay usually shows a success message or redirects
            page_source = driver.page_source.lower()
            
            if "message sent" in page_source or "question sent" in page_source or "successfully sent" in page_source:
                return {
                    "success": True,
                    "message": f"Message sent successfully to seller via item {item_id}"
                }
            else:
                return {
                    "success": True,
                    "message": f"Message likely sent (no error detected). Please check your eBay messages to confirm.",
                    "warning": "Could not explicitly confirm success"
                }
            
        except TimeoutException:
            return {
                "success": False,
                "message": "Timeout waiting for page elements. eBay's interface may have changed or the page loaded slowly."
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Exception occurred during automation: {str(e)}",
            "error_type": type(e).__name__
        }
    
    finally:
        # Always close the browser
        if driver:
            try:
                driver.quit()
            except:
                pass
