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
            "-c", "/usr/share/subjack/fingerprints.json",  
            "-o", "subjack_results.txt", "-v"
        ])
    except Exception as e:
        print(f"[!] subjack failed: {e}")

    print("[+] Running BadDNS...")
    
    # Run dnsx (used by BadDNS)
    try:
        result = subprocess.run(
            ["dnsx", "-l", "subs.txt", "-o", "dnsx_output.txt"],
            capture_output=True, text=True
        )
    except Exception as e:
        print(f"[!] BadDNS failed: {e}")
    
    results = {
        "subjack": set(),
        "baddns": set()
    }
    
    # Read Subjack Results
    try:
        with open("subjack_results.txt", "r") as f:
            for line in f:
                if line.strip():
                    results["subjack"].add(line.strip())
    except FileNotFoundError:
        print("[!] subjack_results.txt not found.")
    
    # Read BadDNS (dnsx) Results
    try:
        with open("dnsx_output.txt", "r") as f:  # ✅ Correct filename!
            for line in f:
                if "Possible Takeover" in line or "Vulnerable" in line:
                    results["baddns"].add(line.strip())
    except FileNotFoundError:
        print("[!] dnsx_output.txt not found.")  # ✅ Corrected filename
    
    # ✅ Corrected keys and filenames in print and return statements
    print(f"[✓] {len(results['subjack'])} unique potential takeovers found by subjack.")
    print(f"[✓] {len(results['baddns'])} unique potential takeovers found by BadDNS.")
    
    return {
        "subjack": sorted(results["subjack"]),
        "baddns": sorted(results["baddns"])
    }
