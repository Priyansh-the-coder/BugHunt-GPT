# core/recon/subdomain_takeover.py

import subprocess
import os
import re

def check_takeover(subdomains):
    print("[+] Writing input subdomains to 'live_subs.txt'")
    with open("live_subs.txt", "w") as f:
        for sub in subdomains:
            cleaned = sub.replace("https://", "").replace("http://", "").strip()
            f.write(cleaned + "\n")

    print("[+] Running subjack...")
    try:
        subprocess.run([
            "subjack", "-w", "live_subs.txt",
            "-t", "100", "-timeout", "30", "-ssl",
            "-c", "/usr/share/subjack/fingerprints.json",
            "-o", "subjack_results.txt", "-v"
        ])
    except Exception as e:
        print(f"[!] subjack failed: {e}")

    print("[+] Running BadDNS (dnsx)...")
    try:
        subprocess.run(
            ["dnsx", "-l", "live_subs.txt", "-o", "dnsx_output.txt"],
            capture_output=True, text=True
        )
    except Exception as e:
        print(f"[!] BadDNS failed: {e}")

    subjack_data = {}
    try:
        with open("subjack_results.txt", "r") as f:
            for line in f:
                # Example line: blog.example.com -> username.github.io [404] There isn't a GitHub Pages site here
                match = re.match(r"(.+?)\s*->\s*(.+?)\s*\[(\d{3})\]\s*(.+)", line.strip())
                if match:
                    subdomain, cname, status_code, body = match.groups()
                    subjack_data[subdomain.strip()] = {
                        "cname": cname.strip(),
                        "status_code": int(status_code),
                        "response_body": body.strip(),
                        "tool_detected": True
                    }
    except FileNotFoundError:
        print("[!] subjack_results.txt not found.")

    baddns_data = set()
    try:
        with open("dnsx_output.txt", "r") as f:
            for line in f:
                line = line.strip()
                for sub in subdomains:
                    sub_clean = sub.replace("https://", "").replace("http://", "").strip()
                    if sub_clean in line and ("Possible Takeover" in line or "Vulnerable" in line):
                        baddns_data.add(sub_clean)
    except FileNotFoundError:
        print("[!] dnsx_output.txt not found.")

    final_results = []

    for sub in subdomains:
        sub_clean = sub.replace("https://", "").replace("http://", "").strip()

        result = {
            "subdomain": sub_clean,
            "cname": subjack_data.get(sub_clean, {}).get("cname", None),
            "status_code": subjack_data.get(sub_clean, {}).get("status_code", None),
            "response_body": subjack_data.get(sub_clean, {}).get("response_body", None),
            "tool_detected": sub_clean in subjack_data or sub_clean in baddns_data
        }

        final_results.append(result)

    print(f"[✓] Formatted output for {len(final_results)} subdomains.")
    return final_results
