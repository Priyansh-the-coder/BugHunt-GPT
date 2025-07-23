# core/recon/url_collector.py

import subprocess
import os

def run_gau(domain, output_file="urls_gau.txt"):
    print(f"[+] Running gau on {domain}")
    try:
        result = subprocess.run(
            ["gau", domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        urls = result.stdout.strip().split("\n")
        with open(output_file, "w") as f:
            f.write("\n".join(urls))
        return urls
    except Exception as e:
        print(f"[!] gau error: {e}")
        return []

def run_waybackurls(domain, output_file="urls_wayback.txt"):
    print(f"[+] Running waybackurls on {domain}")
    try:
        result = subprocess.run(
            ["waybackurls"],
            input=domain,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        urls = result.stdout.strip().split("\n")
        with open(output_file, "w") as f:
            f.write("\n".join(urls))
        return urls
    except Exception as e:
        print(f"[!] waybackurls error: {e}")
        return []

def collect_urls(domain):
    gau_urls = run_gau(domain)
    wayback_urls = run_waybackurls(domain)

    all_urls = list(set(gau_urls + wayback_urls))
    print(f"[✓] Collected {len(all_urls)} unique URLs.")
    return all_urls
