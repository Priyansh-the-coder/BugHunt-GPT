from playwright.async_api import async_playwright
import httpx
import asyncio
from urllib.parse import urlparse
import os


async def capture_data(url):
    # Parse target host for filtering
    target_host = urlparse(url).netloc
    
    result = {
        "server_response": None,
        "browser_requests": []
    }

    # 1. Capture raw server response
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, follow_redirects=True)
            result["server_response"] = {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "content": resp.text,
                "final_url": str(resp.url)
            }
        except Exception as e:
            result["server_response"] = {"error": str(e)}

    # 2. Capture browser requests to target host only
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_page()
        page = await context.new_page()

        def log_request(request):
            if target_host in request.url:
                result["browser_requests"].append({
                    "method": request.method,
                    "url": request.url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data
                })

        page.on("request", log_request)

        try:
            await page.goto(url, wait_until="networkidle", timeout=15000)
        except Exception as e:
            result["browser_error"] = str(e)
        finally:
            await browser.close()

    return result
