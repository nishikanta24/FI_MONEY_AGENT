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

async def get_single_tool_data(session, tool_name):
    try:
        print(f"🔧 Calling tool: {tool_name}")
        response = await session.call_tool(tool_name, {})
        
        if response.content and response.content[0].text.strip():
            try:
                data = json.loads(response.content[0].text)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to decode JSON: {e}")
                return None

            if data.get("status") == "login_required":
                print("🔐 Login required. Open this URL in browser:")
                print(data["login_url"])
                input("Log in and press Enter once done...")
                return await get_single_tool_data(session, tool_name)
            else:
                print(f"✅ {tool_name} data received!")
                
                # Save to file
                filename = f"{tool_name}_data.json"
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"💾 Data saved to {filename}")
                
                return data
        else:
            print("⚠️ Empty response.")
            return None
            
    except Exception as e:
        print(f"❌ Error calling {tool_name}: {e}")
        return None

async def interactive_mcp_client():
    """Keep session running and allow multiple tool calls"""
    MCP_URL = load_config()
    
    available_tools = [
        "fetch_net_worth",
        "fetch_credit_report", 
        "fetch_epf_details",
        "fetch_mf_transactions",
        "fetch_bank_transactions",
        "fetch_stock_transactions"
    ]
    
    try:
        print(f"🚀 Connecting to: {MCP_URL}")
        async with streamablehttp_client(MCP_URL) as (rs, ws, _):
            async with ClientSession(rs, ws) as session:
                print("🔄 Initializing session...")
                await session.initialize()
                print("✅ Session initialized and ready!")
                print("🎯 You can now run multiple tools without re-login")
                print("=" * 50)
                
                while True:
                    print("\n📋 Available tools:")
                    for i, tool in enumerate(available_tools, 1):
                        print(f"  {i}. {tool}")
                    print("  0. Exit")
                    
                    choice = input("\nSelect tool (number or name) or 'exit': ").strip().lower()
                    
                    if choice in ['0', 'exit', 'quit', 'q']:
                        print("👋 Closing session. Goodbye!")
                        break
                    
                    # Handle numeric choice
                    if choice.isdigit():
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(available_tools):
                            tool_name = available_tools[choice_num - 1]
                        else:
                            print("❌ Invalid choice")
                            continue
                    else:
                        tool_name = choice
                        if tool_name not in available_tools:
                            print("❌ Invalid tool name")
                            continue
                    
                    print(f"\n🎯 Running: {tool_name}")
                    print("-" * 30)
                    
                    result = await get_single_tool_data(session, tool_name)
                    
                    if result:
                        print("🎉 Success! Data retrieved and saved.")
                    else:
                        print("❌ Failed to get data.")
                    
                    print("=" * 50)
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(interactive_mcp_client())