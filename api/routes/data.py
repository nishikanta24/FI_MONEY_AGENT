from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
import asyncio
import datetime
from pathlib import Path
import json

# Add src directory to Python path to import connection.py
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connection import automated_mcp_client

router = APIRouter()

@router.get("/fetch-data")
async def fetch_data():
    """
    This is your 'Enter' button - fetches all financial data after authentication
    Runs all 6 tools: net_worth, credit_report, epf, mf_transactions, bank_transactions, stock_transactions
    """
    try:
        # Set mode to fastapi for non-blocking operation
        os.environ["MODE"] = "fastapi"
        
        print("🚀 Frontend triggered data fetch...")
        
        # Call the MCP client with retry logic (same function as auth, but after login)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await automated_mcp_client()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"⚠️  Attempt {attempt + 1} failed, retrying in 1.5s...")
                await asyncio.sleep(1.5)
        
        if not result:
            raise HTTPException(
                status_code=500, 
                detail="Failed to connect to MCP service"
            )
        
        # If still needs login, user hasn't completed authentication
        if result.get("status") == "login_required":
            return JSONResponse(
                status_code=401,
                content={
                    "status": "login_required",
                    "message": "Please complete authentication first",
                    "login_url": result.get("login_url"),
                    "instructions": "Click the login URL, complete authentication, then try again"
                }
            )
        
        # Handle error status
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Unknown error occurred")
            )
        
        # Success! Save data and return response
        with open("fi_mcp_data.json", "w") as f:
            json.dump(result, f, indent=2)
            
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "All financial data fetched successfully! 🎉",
                "data": result,
                "summary": generate_data_summary(result),
                "total_tools": 6,
                "file_saved": "fi_mcp_data.json",
                "attempts_used": attempt + 1  # 1-based count
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Data fetch error: {str(e)}"
        )

@router.get("/data-status")
async def data_status():
    """Check if data file exists and show summary"""
    try:
        data_file = "fi_mcp_data.json"
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            return {
                "status": "data_available",
                "message": "Financial data file found",
                "summary": generate_data_summary(data),
                "file_path": data_file,
                "last_updated": datetime.datetime.fromtimestamp(
                    os.path.getmtime(data_file)
                ).isoformat()
            }
        else:
            return {
                "status": "no_data",
                "message": "No financial data found. Please fetch data first.",
                "instructions": "Use /fetch-data endpoint to get your financial information"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking data status: {str(e)}"
        }

def generate_data_summary(data):
    """Generate a summary of what data was fetched (like your terminal output)"""
    if not data or not isinstance(data, dict):
        return {"total_tools": 0, "successful": 0, "failed": 6}
    
    summary = {
        "total_tools": 6,
        "successful": 0,
        "failed": 0,
        "tools_status": {}
    }
    
    tool_names = [
        "fetch_net_worth",
        "fetch_credit_report", 
        "fetch_epf_details",
        "fetch_mf_transactions",
        "fetch_bank_transactions",
        "fetch_stock_transactions"
    ]
    
    for tool_name in tool_names:
        tool_data = data.get(tool_name, {})
        
        if tool_data and isinstance(tool_data, dict):
            if tool_data.get("status") == "success" and tool_data.get("data"):
                summary["tools_status"][tool_name] = "✅ Data available"
                summary["successful"] += 1
            elif tool_data.get("data"):
                summary["tools_status"][tool_name] = "⚠️ Partial data"
                summary["failed"] += 1
            else:
                summary["tools_status"][tool_name] = "❌ No data"
                summary["failed"] += 1
        else:
            summary["tools_status"][tool_name] = "❌ No data"
            summary["failed"] += 1
    
    return summary

@router.get("/download-data")
async def download_data():
    """Download the JSON file (optional endpoint for your frontend)"""
    try:
        data_file = "fi_mcp_data.json"
        
        if not os.path.exists(data_file):
            raise HTTPException(
                status_code=404,
                detail="No data file found. Please fetch data first."
            )
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        return JSONResponse(
            status_code=200,
            content=data,
            headers={"Content-Disposition": "attachment; filename=fi_mcp_data.json"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Download error: {str(e)}"
        )
