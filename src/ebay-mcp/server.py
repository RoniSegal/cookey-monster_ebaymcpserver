import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from pydantic import AnyUrl
import logging

from ebayAPItool import get_access_token, make_ebay_api_request, send_message_to_seller

server = Server("mcp-ebay-server")
logger = logging.getLogger("mcp-ebay-server")
logger.setLevel(logging.INFO)


## Logging
@server.set_logging_level()
async def set_logging_level(level: types.LoggingLevel) -> types.EmptyResult:
    logger.setLevel(level.upper())
    await server.request_context.session.send_log_message(
        level="info", data=f"Log level set to {level}", logger="mcp-ebay-server"
    )
    return types.EmptyResult()


## Tools
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    """
    return [
        types.Tool(
            name="list-auction",
            description="Scan ebay for Buy It Now listings. This tool is helpful for finding fixed-price items on ebay. Supports searching by text query or UPC/GTIN.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search on ebay. This should just be a name not a description. Optional if upc is provided.",
                    },
                    "upc": {
                        "type": "string",
                        "description": "The UPC (Universal Product Code) or GTIN to search for. Optional if query is provided.",
                    },
                    "ammount": {
                        "type": "integer",
                        "description": "The ammount of results to fetch. This should be a whole non negative number.",

                    },
                },
                "required": ["ammount"],
            },
        ),
        types.Tool(
            name="message-seller",
            description="Send a message to an eBay seller about a specific item. Useful for asking questions or communicating with sellers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The eBay item ID for the listing you want to ask about.",
                    },
                    "recipient_id": {
                        "type": "string",
                        "description": "The seller's eBay username.",
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject line of your message.",
                    },
                    "message": {
                        "type": "string",
                        "description": "The body of the message you want to send to the seller.",
                    },
                },
                "required": ["item_id", "recipient_id", "subject", "message"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if not arguments:
        raise ValueError("Missing arguments")

    if name == "list-auction":
        query = arguments.get("query")
        upc = arguments.get("upc")
        ammount = arguments.get("ammount")

        if not query and not upc:
            raise ValueError("Missing query or upc - at least one must be provided")

        if not ammount:
            ammount = 1

        CLIENT_ID = "Your Ebay Client ID"          # App ID (Client ID)
        CLIENT_SECRET = "Clint Secret"             # Make a Ebay dev acc to get these
        access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
        search_response = make_ebay_api_request(access_token, query, ammount, upc)

        return [
            types.TextContent(
                type="text",
                text=str(search_response),
            )
        ]
    
    elif name == "message-seller":
        item_id = arguments.get("item_id")
        recipient_id = arguments.get("recipient_id")
        subject = arguments.get("subject")
        message = arguments.get("message")

        if not all([item_id, recipient_id, subject, message]):
            raise ValueError("Missing required arguments: item_id, recipient_id, subject, and message are all required")

        # OAuth user token required for messaging (not client credentials)
        USER_TOKEN = "Your Ebay User OAuth Token"  # User OAuth token with messaging permissions
        APP_ID = "Your Ebay App ID"                # Your eBay application ID
        
        response = send_message_to_seller(USER_TOKEN, APP_ID, item_id, recipient_id, subject, message)

        return [
            types.TextContent(
                type="text",
                text=str(response),
            )
        ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-ebay-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
