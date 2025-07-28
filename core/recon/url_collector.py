import subprocess
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
EXTENSION_BLACKLIST = {".jpg", ".png", ".css", ".js", ".svg", ".woff", ".ttf", ".ico"}
STATIC_EXTENSIONS_RE = re.compile(
    r".*\.(?:jpg|png|css|js|svg|woff|ttf|ico)(?:\?.*)?$", 
    re.IGNORECASE
)

def run_tool(command, input_text=None):
    try:
        result = subprocess.run(
            command,
            input=input_text,
            capture_output=True,  # More efficient than separate stdout/stderr
            text=True,
            check=True  # Raises exception on non-zero exit code
        )
        return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running {' '.join(command)}: {e.stderr}")
        return []
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return []

def is_valid_url(url):
    url = url.strip()
    return (url.startswith(("http://", "https://")) and 
            not STATIC_EXTENSIONS_RE.match(url))

def clean_urls(urls):
    seen = set()
    cleaned = []
    for url in urls:
        if not url:
            continue
        clean_url = url.split("#")[0].strip()
        if clean_url and is_valid_url(clean_url) and clean_url not in seen:
            seen.add(clean_url)
            cleaned.append(clean_url)
    return cleaned

def run_tools_concurrently(domain):
    with ThreadPoolExecutor(max_workers=2) as executor:
        gau_future = executor.submit(run_gau, domain)
        wayback_future = executor.submit(run_waybackurls, domain)
        
        results = []
        for future in as_completed([gau_future, wayback_future]):
            results.extend(future.result())
        return results

def run_gau(domain):
    print(f"[+] Running gau on {domain}")
    return run_tool(["gau", "--threads", "10", domain])  # Use gau's built-in threading

def run_waybackurls(domain):
    print(f"[+] Running waybackurls on {domain}")
    return run_tool(["waybackurls"], input_text=domain)

def group_similar_urls(urls):
    grouped = defaultdict(lambda: defaultdict(set))
    no_params = set()

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

    grouped_urls = []
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

def collect_urls(domain, max_urls=3000):
    # Run tools in parallel
    combined = run_tools_concurrently(domain)
    
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
