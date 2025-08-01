import asyncio
import shutil
from typing import List, Set


async def run_tool(command: List[str]) -> List[str]:
    """Run a subdomain enumeration tool asynchronously and return results"""
    try:
        if shutil.which(command[0]) is None:
            return [f"[!] Tool not found: {command[0]}"]
        
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return [f"[!] Failed: {' '.join(command)} - {stderr.decode().strip()}"]
        
        return [
            line.strip() for line in stdout.decode().split("\n")
            if line.strip()
        ]

    except Exception as e:
        return [f"[!] Error: {e}"]


async def run_tools_concurrently(domain: str) -> Set[str]:
    """Run subdomain tools in parallel and collect results in memory"""
    tools = [
        ["subfinder", "-d", domain, "-silent"],
        ["cero", domain],
        ["shosubgo", "-d", domain],
    ]

    print(f"[+] Enumerating subdomains for: {domain}")

    all_results = await asyncio.gather(*[run_tool(cmd) for cmd in tools])
    
    # Flatten and deduplicate
    subs = set()
    for result in all_results:
        for sub in result:
            if not sub.startswith("[!]"):  # Filter error lines
                subs.add(sub)
    
    return subs


async def filter_live_subdomains(subdomains: Set[str]) -> List[str]:
    """Filter live subdomains using httpx, all in memory"""
    try:
        if not subdomains:
            return []

        # Pass subdomains to httpx via stdin
        proc = await asyncio.create_subprocess_exec(
            "httpx", "-silent", "-status-code", "-follow-redirects",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        input_data = "\n".join(subdomains).encode()
        stdout, stderr = await proc.communicate(input=input_data)

        if proc.returncode != 0:
            return [f"[!] httpx error: {stderr.decode().strip()}"]

        # Parse live subdomains
        live_subs = [
            line.strip().split()[0]
            for line in stdout.decode().split("\n")
            if line.startswith("http")
        ]

        print(f"[✓] Found {len(live_subs)} live subdomains.")
        return live_subs

    except Exception as e:
        return [f"[!] Error filtering live subdomains: {e}"]


async def enumerate_subdomains_async(domain: str) -> List[str]:
    """Async implementation of subdomain enumeration"""
    found_subs = await run_tools_concurrently(domain)
    return await filter_live_subdomains(found_subs)


# Sync wrapper for Flask or synchronous use
def enumerate_subdomains(domain: str) -> List[str]:
    return asyncio.run(enumerate_subdomains_async(domain))
