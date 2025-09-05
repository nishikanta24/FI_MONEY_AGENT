


import asyncio
from .connection import interactive_mcp_client

def main():
    print("🚀 Fi Money MCP Client - Persistent Session")
    print("=" * 50)
    print("💡 This will keep you logged in for multiple tool calls")
    print("💡 No need to re-login between different tools")
    print("=" * 50)
    
    # Run the interactive async client
    asyncio.run(interactive_mcp_client())

if __name__ == "__main__":
    main()

