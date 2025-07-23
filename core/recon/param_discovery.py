import subprocess
import os
from urllib.parse import urlparse, parse_qs

def extract_parameters(urls):
    param_names = set()
    param_map = {}

    for url in urls:
        parsed = urlparse(url)
        query = parsed.query
        params = parse_qs(query)

        for param in params:
            param_names.add(param)
            if param not in param_map:
                param_map[param] = []
            param_map[param].append(url)

    return param_names, param_map


def run_paramspider(domain):
    print(f"[+] Running ParamSpider on: {domain}")

    paramspider_dir = os.environ.get("PARAMSPIDER_PATH", "/opt/ParamSpider")
    results_dir = "results"
    output_file = os.path.join(results_dir, f"{domain}.txt")

    # Ensure results folder exists
    os.makedirs(results_dir, exist_ok=True)

    try:
        subprocess.run([
            "python3", "-m", "paramspider.main",
            "-d", domain
        ], check=True, cwd=paramspider_dir, env={**os.environ, "PYTHONPATH": paramspider_dir})
    except subprocess.CalledProcessError as e:
        print(f"[!] ParamSpider error: {e}")

    print(f"[DEBUG] Absolute path to output: {os.path.abspath(output_file)}")
    return output_file if os.path.exists(output_file) else None


def run_arjun(url_file, output_file="arjun_out.txt"):
    print(f"[+] Running Arjun on collected URLs...")
    try:
        subprocess.run([
            "python3", "arjun/arjun.py",
            "--urls", url_file,
            "--output", output_file,
            "--threads", "10"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Arjun error: {e}")
    return output_file if os.path.exists(output_file) else None


def discover_all_parameters(domain):
    paramspider_file = run_paramspider(domain)
    arjun_file = None
    collected_urls = set()

    if paramspider_file and os.path.exists(paramspider_file):
        with open(paramspider_file, "r") as f:
            for line in f:
                url = line.strip()
                if "?" in url:
                    collected_urls.add(url)

    if paramspider_file:
        arjun_file = run_arjun(paramspider_file)

    if arjun_file:
        with open(arjun_file, "r") as f:
            for line in f:
                url = line.strip()
                if "?" in url:
                    collected_urls.add(url)

    print(f"[✓] Total URLs with parameters collected: {len(collected_urls)}")

    return extract_parameters(list(collected_urls))
