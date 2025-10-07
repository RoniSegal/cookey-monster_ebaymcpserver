# Ebay MCP server

Simple Ebay server that lets you fetch Buy It Now listings from Ebay.com

Uses the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) to handle protocol communication and server interactions.

## Example

Let's you use prompts like:
- "Find me 10 Buy It Now listings for batman comics"
- "Search eBay Buy It Now listings by UPC 883028944163"
- "Find fixed-price items with UPC 883028944163"

## Components

### Tools

The server provides a single tool:

- list_auction: Scan ebay for Buy It Now listings (fixed-price items). This tool is helpful for finding fixed-price items on ebay. Supports searching by text query or UPC/GTIN.
  - Optional "query" argument for the search query (text-based search)
  - Optional "upc" argument for UPC/GTIN product code search
    - At least one of "query" or "upc" must be provided
    - Both can be used together to refine searches
  - Required "ammount" argument for ammount of results
    - Must be a non-negative integer
  - Returns result from Ebay's REST API (Buy It Now / fixed-price listings only)

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

### Environment Variables

The following environment variable is required; you can find them on the [Ebay developer portal](https://developer.ebay.com/develop)

- `CLIENT_ID`: Your Ebay client ID
- `CLIENT_SECRET`: Your Ebay client secret
