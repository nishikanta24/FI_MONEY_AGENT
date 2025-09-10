import asyncio
import logging
import os
from typing import Optional, Dict

from src.connection import automated_mcp_client

# Module-level items
run_lock = asyncio.Lock()
logger = logging.getLogger(__name__)
_last_result: Optional[Dict] = None

async def _run_mcp_with_retry(
    max_retries: int = 3, 
    retry_delay: float = 1.5
) -> Dict:
    """
    Internal helper to run MCP client with retry logic and lock protection.
    Returns normalized response dict.
    """
    global _last_result
    attempts = 0
    last_exception = None

    async with run_lock:
        original_mode = os.environ.get("MODE")
        os.environ["MODE"] = "fastapi"

        try:
            for attempt in range(1, max_retries + 1):
                attempts = attempt
                try:
                    result = await automated_mcp_client()
                    # Check for login_required status
                    if result.get("status") == "login_required":
                        _last_result = {
                            "status": "login_required",
                            "login_url": result.get("login_url"),
                            "attempts": attempts
                        }
                        logger.info(f"MCP operation returned login_required after {attempts} attempt(s)")
                        return _last_result
                    else:
                        _last_result = {
                            "status": "success",
                            "data": result,
                            "attempts": attempts
                        }
                        logger.info(f"MCP operation succeeded after {attempts} attempt(s)")
                        return _last_result

                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"MCP attempt {attempt} failed, retrying in {retry_delay}s - {str(e)}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.exception("MCP operation failed after max retries")
                        _last_result = {
                            "status": "error",
                            "error": str(e),
                            "attempts": attempts
                        }
                        return _last_result

        finally:
            if original_mode:
                os.environ["MODE"] = original_mode
            else:
                os.environ.pop("MODE", None)

async def authenticate_mcp(
    max_retries: int = 2, 
    retry_delay: float = 1.5
) -> Dict:
    """
    Authenticate with MCP service with retry logic.
    Returns normalized response dict with status, data, and attempts.
    """
    result = await _run_mcp_with_retry(max_retries, retry_delay)
    # Just return the normalized result from _run_mcp_with_retry
    return result

async def fetch_mcp_data(
    max_retries: int = 3, 
    retry_delay: float = 1.5
) -> Dict:
    """
    Fetch data from MCP service with retry logic.
    Returns normalized response dict with status, data, and attempts.
    """
    result = await _run_mcp_with_retry(max_retries, retry_delay)
    return result

def last_cached_result() -> Optional[Dict]:
    """Get the last cached result from MCP operations"""
    return _last_result
