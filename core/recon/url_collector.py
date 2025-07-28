# core/recon/url_collector.py

import subprocess
import os
import re

EXTENSION_BLACKLIST = [".jpg", ".png", ".css", ".js", ".svg", ".woff", ".ttf", ".ico"]
STATIC_EXTENSIONS_RE = re.compile(r".*\.(" + "|".join([e.lstrip('.') for e in EXTENSION_BLACKLIST]) + r")(\?.*)?$", re.IGNORECASE)

def run_tool(command, input_text=None):
    try:
        result = subprocess.run(
            command,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        urls = result.stdout.strip().split("\n")
        return urls
    except Exception as e:
        print(f"[!] Error running {' '.join(command)}: {e}")
        return []

def is_valid_url(url):
    if STATIC_EXTENSIONS_RE.match(url):
        return False
    if url.startswith("http") and "://" in url:
        return True
    return False

def clean_urls(urls):
    # Deduplicate, normalize, and filter
    cleaned = set()
    for url in urls:
        url = url.strip()
        if is_valid_url(url):
            cleaned.add(url.split("#")[0])  # Remove fragments
    return list(cleaned)

def run_gau(domain):
    print(f"[+] Running gau on {domain}")
    return run_tool(["gau", domain])

def run_waybackurls(domain):
    print(f"[+] Running waybackurls on {domain}")
    return run_tool(["waybackurls"], input_text=domain)

def collect_urls(domain, max_urls=3000):
    gau_urls = run_gau(domain)
    wayback_urls = run_waybackurls(domain)

    combined = gau_urls + wayback_urls
    cleaned = clean_urls(combined)

    # Optional: Sort by priority (URLs with params come first)
    sorted_urls = sorted(cleaned, key=lambda u: ('?' not in u, len(u)))

    final_urls = sorted_urls[:max_urls]  # Limit total token size
    print(f"[✓] Final URL count (after dedup/filter): {len(final_urls)}")

    # # Save output
    # os.makedirs("output", exist_ok=True)
    # with open(f"output/{domain}_urls.txt", "w") as f:
    #     f.write("\n".join(final_urls))

    return final_urls
