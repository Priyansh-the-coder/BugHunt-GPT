from playwright.async_api import async_playwright
import httpx
from urllib.parse import urlparse
from typing import Dict, List, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_data(url: str) -> Dict[str, Union[Dict, List, str]]:
    """
    Capture server response and browser requests for a given URL.
    
    Args:
        url: The target URL to capture data from
        
    Returns:
        Dictionary containing:
        - server_response: Raw HTTP response from server
        - browser_requests: List of requests made by browser to target host
        - error: Optional error message if something failed
    """
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    target_host = urlparse(url).netloc
    result = {
        "server_response": None,
        "browser_requests": [],
        "error": None
    }

    # 1. Capture raw server response with timeout
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                url,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            result["server_response"] = {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "content": resp.text[:5000] + "..." if len(resp.text) > 5000 else resp.text,
                "final_url": str(resp.url),
                "response_time_ms": resp.elapsed.microseconds / 1000
            }
        except Exception as e:
            logger.error(f"Server request failed: {str(e)}")
            result["server_response"] = {"error": str(e)}
            result["error"] = f"Server request failed: {str(e)}"

    # 2. Capture browser requests with proper cleanup
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                timeout=10000,
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            page = await context.new_page()

            def log_request(request):
                try:
                    if target_host in request.url:
                        result["browser_requests"].append({
                            "method": request.method,
                            "url": request.url,
                            "headers": dict(request.headers),
                            "post_data": request.post_data,
                            "resource_type": request.resource_type,
                            "timestamp": request.timestamp
                        })
                except Exception as e:
                    logger.warning(f"Failed to log request: {str(e)}")

            page.on("request", log_request)

            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=15000,
                    referer=None
                )
            except Exception as e:
                logger.error(f"Browser navigation failed: {str(e)}")
                result["error"] = f"Browser navigation failed: {str(e)}"
            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        logger.error(f"Playwright failed: {str(e)}")
        result["error"] = f"Playwright failed: {str(e)}"

    # Clean up potentially sensitive headers
    for request in result["browser_requests"]:
        for header in ['cookie', 'authorization']:
            if header in request["headers"]:
                request["headers"][header] = "[REDACTED]"

    return result
