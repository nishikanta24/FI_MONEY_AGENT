from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
import asyncio
from pathlib import Path

# Add src directory to Python path to import connection.py
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from connection import automated_mcp_client

router = APIRouter()

@router.get("/authenticate")
async def authenticate():
    """
    Authenticate with Fi Money MCP service
    Returns login URL if authentication needed, or full data if already authenticated
    """
    try:
        # Set mode to fastapi for non-blocking operation
        os.environ["MODE"] = "fastapi"
        
        # Call the MCP client with retry logic
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to connect to MCP service")
                result = await automated_mcp_client()
                break
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"Retry attempt {attempt + 1} failed, retrying in 1.5 seconds...")
                    await asyncio.sleep(1.5)
                else:
                    print("All retry attempts failed")
                    raise
        
        if not result:
            raise HTTPException(
                status_code=500, 
                detail="Failed to connect to MCP service"
            )
        
        # Check if login is required
        if result.get("status") == "login_required":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "login_required",
                    "message": "Please login to Fi Money to continue",
                    "login_url": result.get("login_url"),
                    "instructions": "Open the login URL in your browser, complete login, then call /fetch-data"
                }
            )
        
        # If we have data, authentication was successful
        elif result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Unknown error occurred")
            )
        
        # Authentication successful, return data
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Authentication successful and data retrieved",
                "data": result
            }
        )
        
    except Exception as e:
        import traceback
        # Print full traceback to console for debugging
        print("❌ ERROR in /authenticate:", traceback.format_exc())

        # Return a clearer error in API response
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {repr(e)}"

        )

@router.get("/status")
async def auth_status():
    """Check authentication status without triggering login flow"""
    return {
        "status": "ready",
        "message": "Authentication endpoint is ready",
        "mode": os.getenv("MODE", "fastapi"),
        "instructions": "Call /authenticate to start the login flow"
    }
