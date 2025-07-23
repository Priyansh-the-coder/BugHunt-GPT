# core/recon/subdomain_takeover.py

import subprocess

def check_takeover(subdomains):
    print("[+] Writing input subdomains to 'live_subs.txt'")
    with open("live_subs.txt", "w") as f:
        for sub in subdomains:
            f.write(sub.replace("https://", "").replace("http://", "").strip() + "\n")

    print("[+] Running subjack...")
    try:
        subprocess.run([
            "subjack", "-w", "live_subs.txt",
            "-t", "100", "-timeout", "30", "-ssl",
            "-c", "/path/to/fingerprints.json",  # ⚠️ Update this path
            "-o", "subjack_results.txt", "-v"
        ])
    except Exception as e:
        print(f"[!] subjack failed: {e}")

    print("[+] Running BadDNS...")
    try:
        subprocess.run([
            "baddns", "-i", "live_subs.txt", "-o", "baddns_results.txt", "-t", "100"
        ])
    except Exception as e:
        print(f"[!] BadDNS failed: {e}")

    results = {
        "subjack": set(),
        "baddns": set()
    }

    try:
        with open("subjack_results.txt", "r") as f:
            for line in f:
                if line.strip():
                    results["subjack"].add(line.strip())
    except FileNotFoundError:
        print("[!] subjack_results.txt not found.")

    try:
        with open("baddns_results.txt", "r") as f:
            for line in f:
                if "Possible Takeover" in line or "Vulnerable" in line:
                    results["baddns"].add(line.strip())
    except FileNotFoundError:
        print("[!] baddns_results.txt not found.")

    print(f"[✓] {len(results['subjack'])} unique potential takeovers found by subjack.")
    print(f"[✓] {len(results['baddns'])} unique potential takeovers found by BadDNS.")

    return {
        "subjack": sorted(results["subjack"]),
        "baddns": sorted(results["baddns"])
    }
