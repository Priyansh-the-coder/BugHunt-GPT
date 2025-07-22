import subprocess

def enumerate_subdomains(domain):
    all_subs_file = "all_subs.txt"
    live_subs = []

    # Clean previous data
    open(all_subs_file, 'w').close()

    print(f"[+] Enumerating subdomains for: {domain}")

    # Passive Enumeration
    subprocess.run(["subfinder", "-d", domain, "-silent"], stdout=open(all_subs_file, "a"), check=True)
    print("[+] Run subfinder done")
    subprocess.run(["assetfinder", "--subs-only", domain], stdout=open(all_subs_file, "a"), check=True)
    print("[+] Run assetfinder done")
    '''result = subprocess.run(
        ["amass", "enum", "-passive", "-d", domain, "-rf", '/root/BugHunt-GPT/core/recon/resolvers.txt'],
   	stdout=open(all_subs_file, "a"),
   	stderr=subprocess.PIPE,
    	text=True
	)

    if result.returncode != 0:
    	print(f"[!] Amass failed:\n{result.stderr}")
    	return []
    else:
    	print("[✓] Amass completed successfully.")
    '''
    print("[+] Run amass done")

    '''subprocess.run(["sublist3r", "-d", domain, "-o", "sublister_out.txt"], check=True)
    print("[+] Run sublist3r done")
    with open("sublister_out.txt", "r") as f:
       with open(all_subs_file, "a") as af:
            af.write(f.read())
    '''
    subprocess.run(["cero", domain], stdout=open(all_subs_file, "a"), check=True)
    print("[+] Running cero done")
    subprocess.run(["shosubgo", "-d", domain], stdout=open(all_subs_file, "a"), check=True)
    print("[+] Running shosubgo done")

    # Active Enumeration
    '''subprocess.run([
        "puredns", "resolve", "wordlists/all.txt",
        "-r", "resolvers.txt",
        "-w", "puredns_out.txt", "--wildcard-tests", domain
    ], check=True, timeout=300)
    print("[+] Running puredns done")
    with open("puredns_out.txt", "r") as f:
        with open(all_subs_file, "a") as af:
            af.write(f.read())
    
    subprocess.run(["python3", "subbrute/subbrute.py", domain], stdout=open("subbrute_out.txt", "w"), check=True)
    print("[+] Running subbrute done")
    with open("subbrute_out.txt", "r") as f:
        with open(all_subs_file, "a") as af:
            af.write(f.read())

    subprocess.run([
        "ffuf", "-u", f"https://FUZZ.{domain}", "-w", "wordlists/subdomains.txt",
        "-mc", "200,301,302", "-o", "ffuf_out.txt", "-of", "csv"
    ], check=True)
    print("[+] Running ffuf done")
    with open("ffuf_out.txt", "r") as f:
        for line in f:
            if line.startswith("http"):
                sub = line.strip().split(",")[0].split("//")[-1].split("/")[0]
                with open(all_subs_file, "a") as af:
                    af.write(sub + "\n")
    '''
    # Deduplicate
    with open(all_subs_file, "r") as f:
        unique_subs = sorted(set(line.strip() for line in f if line.strip() and domain in line))

    with open("subs.txt", "w") as out:
        out.write("\n".join(unique_subs))

    # Check live subdomains with httpx
    try:
        output = subprocess.check_output(
            ["/root/go/bin/httpx", "-l", "subs.txt", "-silent", "-status-code", "-follow-redirects"],
            text=True
        )
        for line in output.strip().split("\n"):
            if line.startswith("http"):
                url = line.strip().split()[0]
                live_subs.append(url)

        print(f"[✓] Found {len(live_subs)} live subdomains.")
        return live_subs

    except subprocess.CalledProcessError as e:
        print(f"[!] httpx error: {e}")
        return []
