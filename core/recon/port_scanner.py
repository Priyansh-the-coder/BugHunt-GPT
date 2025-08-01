# core/scan/port_scanner.py

import subprocess
from io import StringIO

def scan_ports(domain):
    print(f"[+] Starting Nmap port scan on: {domain}")
    scan_results = []

    try:
        # Run nmap and capture output directly to memory
        result = subprocess.run([
            "nmap","-T4", "-A", "-v",  domain
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[!] Nmap scanning failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return []
            
        # Process the output directly from memory
        output = result.stdout
        for line in StringIO(output):
            line = line.strip()
            if line and ("/tcp" in line or "/udp" in line) and ("open" in line):
                scan_results.append(line)
                
    except Exception as e:
        print(f"[!] Nmap scanning failed: {e}")
        return []

    print(f"[✓] Found {len(scan_results)} open ports.")
    return scan_results
