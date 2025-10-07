import base64
import json
import os
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

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

# Function to send a message to an eBay seller using the Trading API
def send_message_to_seller(user_token, app_id, item_id, recipient_id, subject, message_body):
    """
    Send a message to an eBay seller about a specific item.
    Uses eBay's Trading API (XML/SOAP) with the AddMemberMessageAAQToPartner call.
    
    Args:
        user_token: OAuth user token with messaging permissions
        app_id: Your eBay application ID (App ID)
        item_id: The eBay item ID
        recipient_id: The seller's eBay username
        subject: Message subject
        message_body: Message content
    
    Returns:
        Dictionary with success status and message
    """
    # eBay Trading API endpoint (use production or sandbox)
    # Production: https://api.ebay.com/ws/api.dll
    # Sandbox: https://api.sandbox.ebay.com/ws/api.dll
    url = "https://api.ebay.com/ws/api.dll"
    
    # Build XML request for AddMemberMessageAAQToPartner
    xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<AddMemberMessageAAQToPartnerRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{user_token}</eBayAuthToken>
    </RequesterCredentials>
    <ItemID>{item_id}</ItemID>
    <MemberMessage>
        <Subject>{subject}</Subject>
        <Body>{message_body}</Body>
        <QuestionType>CustomizedSubject</QuestionType>
        <RecipientID>{recipient_id}</RecipientID>
    </MemberMessage>
</AddMemberMessageAAQToPartnerRequest>"""
    
    # Set headers for Trading API
    headers = {
        "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
        "X-EBAY-API-DEV-NAME": app_id,
        "X-EBAY-API-APP-NAME": app_id,
        "X-EBAY-API-CERT-NAME": app_id,
        "X-EBAY-API-SITEID": "0",  # 0 = US site
        "X-EBAY-API-CALL-NAME": "AddMemberMessageAAQToPartner",
        "Content-Type": "text/xml; charset=utf-8",
    }
    
    try:
        response = requests.post(url, data=xml_request.encode('utf-8'), headers=headers)
        
        if response.status_code == 200:
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Check for eBay API errors
            ack = root.find(".//{urn:ebay:apis:eBLBaseComponents}Ack")
            
            if ack is not None and ack.text in ["Success", "Warning"]:
                return {
                    "success": True,
                    "message": "Message sent successfully to seller",
                    "ack": ack.text
                }
            else:
                # Extract error details
                errors = []
                for error in root.findall(".//{urn:ebay:apis:eBLBaseComponents}Errors"):
                    error_code = error.find("{urn:ebay:apis:eBLBaseComponents}ErrorCode")
                    short_message = error.find("{urn:ebay:apis:eBLBaseComponents}ShortMessage")
                    long_message = error.find("{urn:ebay:apis:eBLBaseComponents}LongMessage")
                    
                    error_info = {
                        "code": error_code.text if error_code is not None else "Unknown",
                        "short_message": short_message.text if short_message is not None else "Unknown error",
                        "long_message": long_message.text if long_message is not None else ""
                    }
                    errors.append(error_info)
                
                return {
                    "success": False,
                    "message": "Failed to send message",
                    "errors": errors
                }
        else:
            return {
                "success": False,
                "message": f"HTTP Error: {response.status_code}",
                "details": response.text
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Exception occurred: {str(e)}"
        }
