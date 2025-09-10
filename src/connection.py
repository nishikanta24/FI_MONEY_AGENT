import asyncio
import json
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession
import os

def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['stream_url']

async def get_data(session):
    """Automatically fetch all financial data after authentication"""
    try:
        main_json = {}
        available_tools = [
            "fetch_net_worth",
            "fetch_credit_report", 
            "fetch_epf_details",
            "fetch_mf_transactions",
            "fetch_bank_transactions",
            "fetch_stock_transactions"
        ]
        
        # Check authentication with first tool
        print("🔐 Checking authentication status...")
        response = await session.call_tool("fetch_net_worth", {})
        if response.content and response.content[0].text.strip():
            try:
                data = json.loads(response.content[0].text)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to decode JSON: {e}")
                data = {}

            if data.get("status") == "login_required":
                print("🔐 Login required. Open this URL in browser:")
                print(data["login_url"])
                
                # MODE-based login handling - added for CLI/FastAPI compatibility
                mode = os.getenv("MODE", "fastapi").lower()
                if mode == "cli":
                    input("Press Enter after login...")
                    return await get_data(session)  # Retry after login
                else:
                    return {"status": "login_required", "login_url": data["login_url"]}
            else:
                print("✅ fetch_net_worth data received!")
                main_json["fetch_net_worth"] = data
        else:
            print("⚠️ Empty response for fetch_net_worth")
            main_json["fetch_net_worth"] = {}
        
        # Execute all remaining tools in parallel
        remaining_tools = available_tools[1:]
        print("🚀 Executing tools in parallel...")
        
        async def fetch_tool_data(tool_name):
            try:
                response = await session.call_tool(tool_name, {})
                if response.content and response.content[0].text.strip():
                    try:
                        data = json.loads(response.content[0].text)
                        print(f"✅ {tool_name} data received!")
                        return (tool_name, data)
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to decode JSON for {tool_name}: {e}")
                        return (tool_name, {})
                else:
                    print(f"⚠️ Empty response for {tool_name}")
                    return (tool_name, {})
            except Exception as e:
                print(f"❌ Error calling {tool_name}: {e}")
                return (tool_name, {})
        
        # Run all tools concurrently
        results = await asyncio.gather(*[fetch_tool_data(tool) for tool in remaining_tools])
        
        # Add results to main JSON
        for tool_name, data in results:
            main_json[tool_name] = data
        
        # Save consolidated data to single file
        filename = "fi_mcp_data.json"
        with open(filename, "w") as f:
            json.dump(main_json, f, indent=4)
        
        print(f"\n🎉 All data fetched successfully!")
        print(f"💾 Consolidated data saved to {filename}")
        
        # Print summary
        print("\n📊 Data Summary:")
        for tool_name, data in main_json.items():
            if data and isinstance(data, dict):
                if data.get("status") == "success" or "data" in data or len(data) > 1:
                    print(f"  ✅ {tool_name}: Data available")
                else:
                    print(f"  ⚠️  {tool_name}: Limited/No data")
            else:
                print(f"  ❌ {tool_name}: No data")
        
        return main_json
        
    except Exception as e:
        print(f"❌ Error in get_data: {e}")
        return None

async def automated_mcp_client():
    """Automated MCP client - fetches all data after single login"""
    MCP_URL = load_config()
    
    try:
        print(f"🚀 Connecting to: {MCP_URL}")
        async with streamablehttp_client(MCP_URL) as (rs, ws, _):
            async with ClientSession(rs, ws) as session:
                print("🔄 Initializing session...")
                await session.initialize()
                print("✅ Session initialized!")
                print("🎯 Starting parallel data fetch...")
                print("=" * 50)
                
                result = await get_data(session)
                
                if result:
                    if result.get("status") == "login_required":
                        return result
                    print("\n🎊 Success! All financial data has been consolidated.")
                    return result
                else:
                    print("\n❌ Failed to fetch data.")
                    return {"status": "error", "message": "Failed to fetch data"}
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("🤖 Fi Money MCP Client - Automated Mode")
    print("=" * 30)
    print("🚀 Starting automated data fetch...")
    asyncio.run(automated_mcp_client())
