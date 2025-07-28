import asyncio
import re
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
from typing import List, Set, Dict

# Constants
EXTENSION_BLACKLIST = {".jpg", ".png", ".css", ".js", ".svg", ".woff", ".ttf", ".ico"}
STATIC_EXTENSIONS_RE = re.compile(
    r".*\.(?:jpg|png|css|js|svg|woff|ttf|ico)(?:\?.*)?$", 
    re.IGNORECASE
)

async def run_tool(command: List[str], input_text: str = None) -> List[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE if input_text else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=input_text.encode() if input_text else None)
        
        if proc.returncode != 0:
            print(f"[!] Error running {' '.join(command)}: {stderr.decode().strip()}")
            return []
            
        return stdout.decode().strip().split("\n")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return []

def is_valid_url(url: str) -> bool:
    url = url.strip()
    return (url.startswith(("http://", "https://")) and 
            not STATIC_EXTENSIONS_RE.match(url))

def clean_urls(urls: List[str]) -> List[str]:
    seen: Set[str] = set()
    cleaned: List[str] = []
    for url in urls:
        if not url:
            continue
        clean_url = url.split("#")[0].strip()
        if clean_url and is_valid_url(clean_url) and clean_url not in seen:
            seen.add(clean_url)
            cleaned.append(clean_url)
    return cleaned

async def run_gau(domain: str) -> List[str]:
    print(f"[+] Running gau on {domain}")
    return await run_tool(["gau", "--threads", "10", "--subs", domain])

async def run_waybackurls(domain: str) -> List[str]:
    print(f"[+] Running waybackurls on {domain}")
    return await run_tool(["waybackurls"], input_text=domain)

async def run_tools_concurrently(domain: str) -> List[str]:
    gau_task = asyncio.create_task(run_gau(domain))
    wayback_task = asyncio.create_task(run_waybackurls(domain))
    
    results = []
    for task in asyncio.as_completed([gau_task, wayback_task]):
        results.extend(await task)
    return results

def group_similar_urls(urls: List[str]) -> List[str]:
    grouped: Dict[str, Dict[str, Set[str]] = defaultdict(lambda: defaultdict(set))
    no_params: Set[str] = set()

    for url in urls:
        try:
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            params = parse_qs(parsed.query, keep_blank_values=True)

            if not params:
                no_params.add(base)
                continue

            for key, values in params.items():
                grouped[base][key].update(values)
        except Exception as e:
            print(f"[!] Error parsing URL {url}: {e}")
            continue

    grouped_urls: List[str] = []
    for base, param_map in grouped.items():
        query_parts = []
        for key, values in param_map.items():
            if len(values) == 1:
                query_parts.append(f"{key}={next(iter(values))}")
            else:
                query_parts.append(f"{key}={{{','.join(sorted(values))}}}")
        grouped_urls.append(f"{base}?{'&'.join(query_parts)}")

    grouped_urls.extend(no_params)
    return grouped_urls

async def collect_urls(domain: str, max_urls: int = 3000) -> List[str]:
    # Run tools in parallel
    combined = await run_tools_concurrently(domain)
    
    # Clean and filter URLs
    cleaned = clean_urls(combined)
    
    # Sort with priority to URLs with parameters
    sorted_urls = sorted(
        cleaned,
        key=lambda u: ('?' not in u, len(u)),
    )
    
    # Apply limit
    limited_urls = sorted_urls[:max_urls]
    
    print(f"[✓] Final URL count (after dedup/filter): {len(limited_urls)}")
    
    # Group similar URLs
    return group_similar_urls(limited_urls)

# Example usage:
# asyncio.run(collect_urls("example.com"))
