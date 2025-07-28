import asyncio
import os
from typing import List, Set
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

ALL_SUBS_FILE = "all_subs.txt"
SUBS_FILE = "subs.txt"

async def run_tool(command: List[str], output_file: str = None) -> List[str]:
    """Run a subdomain enumeration tool asynchronously"""
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            print(f"[!] {' '.join(command)} failed: {stderr.decode().strip()}")
            return []
            
        results = stdout.decode().strip().split("\n")
        
        if output_file:
            async with aiofiles.open(output_file, "a") as f:
                await f.write("\n".join(r for r in results if r) + "\n")
                
        return results
        
    except Exception as e:
        print(f"[!] Error running {' '.join(command)}: {e}")
        return []

async def run_tools_concurrently(domain: str) -> None:
    """Run all subdomain tools in parallel"""
    tools = [
        (["subfinder", "-d", domain, "-silent"], ALL_SUBS_FILE),
        (["cero", domain], ALL_SUBS_FILE),
        (["shosubgo", "-d", domain], ALL_SUBS_FILE),
    ]
    
    # Clear previous results
    open(ALL_SUBS_FILE, 'w').close()
    
    print(f"[+] Enumerating subdomains for: {domain}")
    
    # Run all tools concurrently
    await asyncio.gather(*[
        run_tool(cmd, out) for cmd, out in tools
    ])

async def filter_live_subdomains() -> List[str]:
    """Check which subdomains are live using httpx"""
    try:
        # Deduplicate results
        async with aiofiles.open(ALL_SUBS_FILE, "r") as f:
            content = await f.read()
            unique_subs = sorted(set(
                line.strip() for line in content.split("\n") 
                if line.strip()
            ))
            
        # Save unique subdomains
        async with aiofiles.open(SUBS_FILE, "w") as f:
            await f.write("\n".join(unique_subs))
            
        # Check live subdomains
        proc = await asyncio.create_subprocess_exec(
            "httpx", "-l", SUBS_FILE, "-silent", "-status-code", "-follow-redirects",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            print(f"[!] httpx error: {stderr.decode().strip()}")
            return []
            
        live_subs = [
            line.strip().split()[0] 
            for line in stdout.decode().split("\n") 
            if line.startswith("http")
        ]
        
        print(f"[✓] Found {len(live_subs)} live subdomains.")
        return live_subs
        
    except Exception as e:
        print(f"[!] Error filtering live subdomains: {e}")
        return []

async def enumerate_subdomains_async(domain: str) -> List[str]:
    """Async implementation of subdomain enumeration"""
    await run_tools_concurrently(domain)
    return await filter_live_subdomains()

# Sync wrapper for Flask compatibility
def enumerate_subdomains(domain: str) -> List[str]:
    """Original sync interface (no changes needed in main.py)"""
    try:
        import aiofiles  # Optional for async file I/O
    except ImportError:
        aiofiles = None
        print("[!] For optimal performance, install aiofiles: pip install aiofiles")
        
    return asyncio.run(enumerate_subdomains_async(domain))
