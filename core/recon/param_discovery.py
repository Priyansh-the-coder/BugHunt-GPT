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

    return list(param_names), param_map

def run_paramspider(domain):
    print(f"[+] Running ParamSpider on: {domain}")

    paramspider_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ParamSpider"))
    results_dir = os.path.join(paramspider_dir, "results")
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

    return output_file if os.path.exists(output_file) else None

def discover_all_parameters(domain):
    paramspider_file = run_paramspider(domain)
    collected_urls = set()

    if paramspider_file and os.path.exists(paramspider_file):
        with open(paramspider_file, "r") as f:
            for line in f:
                url = line.strip()
                if "?" in url:
                    collected_urls.add(url)

    print(f"[\u2713] Total URLs with parameters collected: {len(collected_urls)}")

    return extract_parameters(list(collected_urls))
