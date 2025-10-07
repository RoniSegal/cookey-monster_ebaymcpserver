# Ebay MCP server

A powerful eBay MCP server that lets you:
- 🔍 Search for Buy It Now listings by text query or UPC/GTIN
- 💬 **Message sellers WITHOUT any prior purchase** (creative browser automation solution!)

Uses the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) to handle protocol communication and server interactions.

## Example

Let's you use prompts like:
- "Find me 10 Buy It Now listings for batman comics"
- "Search eBay Buy It Now listings by UPC 883028944163"
- "Find fixed-price items with UPC 883028944163"
- "Send a message to seller john_doe about item 123456789 asking about shipping"

## Components

### Tools

The server provides two tools:

#### 1. list_auction
Scan ebay for Buy It Now listings (fixed-price items). This tool is helpful for finding fixed-price items on ebay. Supports searching by text query or UPC/GTIN.
- Optional "query" argument for the search query (text-based search)
- Optional "upc" argument for UPC/GTIN product code search
  - At least one of "query" or "upc" must be provided
  - Both can be used together to refine searches
- Required "ammount" argument for ammount of results
  - Must be a non-negative integer
- Returns result from Ebay's REST API (Buy It Now / fixed-price listings only)

#### 2. message-seller
Send a message to an eBay seller about a specific item **WITHOUT any prior interaction** (no purchase, bid, or offer required). This creative solution uses browser automation to simulate clicking the "Contact Seller" button on eBay's website.
- Required "item_id" argument - The eBay item ID for the listing
- Required "subject" argument - The subject/topic of your message
- Required "message" argument - The body of the message
- Returns success status and confirmation message

**How it works:**
- Uses Selenium WebDriver to automate a headless Chrome browser
- Logs into your eBay account
- Navigates to the item page
- Clicks the "Contact Seller" button
- Fills in and submits the message form
- Works even without prior purchases, bids, or offers

**Note:** This requires your eBay login credentials (username and password). See Authentication section below.

## Installation

### Requires [UV](https://github.com/astral-sh/uv) (Fast Python package and project manager)

If uv isn't installed.

```bash
# Using Homebrew on macOS
brew install uv
```

or

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Next, install the MCP server

```bash
# Install from source
uv pip install git+https://github.com/CooKey-Monster/EbayMcpServer.git
```

### Environment Variables / Authentication

#### For Searching Listings (list_auction tool):
You can obtain API credentials from the [eBay developer portal](https://developer.ebay.com/develop)
- `CLIENT_ID`: Your eBay client ID (App ID)
- `CLIENT_SECRET`: Your eBay client secret (Cert ID)

#### For Messaging Sellers (message-seller tool):
This uses browser automation and requires your regular eBay account credentials:
- `EBAY_USERNAME`: Your eBay username or email address
- `EBAY_PASSWORD`: Your eBay account password

**Important Security Notes:**
- The messaging feature uses Selenium browser automation to bypass API limitations
- Your credentials are only used locally to log into eBay via an automated browser
- The browser runs in headless mode (background, no visible window)
- Chrome/Chromium browser is required (automatically managed by webdriver-manager)
- Consider creating a dedicated eBay account for automation if security is a concern

**System Requirements for Messaging:**
- Chrome or Chromium browser must be installed on the system
- The `message-seller` tool will automatically download and manage ChromeDriver
- First run may take longer as it downloads the appropriate driver version
