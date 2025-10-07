# Ebay MCP server

Simple Ebay server that lets you fetch Buy It Now listings from Ebay.com

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
Send a message to an eBay seller about a specific item. Uses eBay's Trading API.
- Required "item_id" argument - The eBay item ID for the listing
- Required "recipient_id" argument - The seller's eBay username
- Required "subject" argument - The subject line of your message
- Required "message" argument - The body of the message
- Returns success status and confirmation message

**Note:** The messaging functionality requires a user OAuth token with messaging permissions, not just client credentials. See Authentication section below.

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

The following credentials are required; you can obtain them from the [eBay developer portal](https://developer.ebay.com/develop)

#### For Searching Listings (list_auction tool):
- `CLIENT_ID`: Your eBay client ID (App ID)
- `CLIENT_SECRET`: Your eBay client secret (Cert ID)

#### For Messaging Sellers (message-seller tool):
- `USER_TOKEN`: OAuth user token with messaging permissions (not client credentials)
- `APP_ID`: Your eBay application ID

**Important:** The messaging functionality uses eBay's Trading API which requires user-level OAuth authentication. This is different from the client credentials used for searching. You'll need to:
1. Set up OAuth consent flow to obtain user tokens
2. Request user permission for messaging scope
3. Store and refresh user tokens appropriately

For more information on obtaining user OAuth tokens, see [eBay's OAuth documentation](https://developer.ebay.com/api-docs/static/oauth-tokens.html)
