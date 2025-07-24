# core/scan/port_scanner.py

import subprocess

def scan_ports(domain):
    print(f"[+] Starting Nmap port scan on: {domain}")
    scan_results = []

    try:
        subprocess.run([
            "nmap", domain, "-sS", "-sV", "-T4", "-Pn",
            "-oN", "nmap_results.txt"
        ])
    except Exception as e:
        print(f"[!] Nmap scanning failed: {e}")
        return []

    print("[+] Parsing Nmap results...")
    try:
        with open("nmap_results.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and ("/tcp" in line or "/udp" in line) and ("open" in line):
                    scan_results.append(line)
    except FileNotFoundError:
        print("[!] nmap_results.txt not found.")
        return []

    print(f"[✓] Found {len(scan_results)} open ports.")
    return scan_results
