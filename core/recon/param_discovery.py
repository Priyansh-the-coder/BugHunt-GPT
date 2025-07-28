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

    try:
        result = subprocess.run(
            ["python3", "-m", "paramspider.main", "-d", domain],
            check=True,
            capture_output=True,
            text=True,
            cwd=paramspider_dir,
            env={**os.environ, "PYTHONPATH": paramspider_dir}
        )
        urls = set()
        for line in result.stdout.splitlines():
            url = line.strip()
            if "?" in url:
                urls.add(url)
        return list(urls)

    except subprocess.CalledProcessError as e:
        print(f"[!] ParamSpider error: {e}")
        return []


def run_arjun(urls):
    print(f"[+] Running Arjun on collected URLs...")

    try:
        input_data = "\n".join(urls).encode()
        result = subprocess.run(
            ["python3", "arjun/arjun.py", "--stdin", "--get", "--threads", "10"],
            input=input_data,
            capture_output=True,
            text=True
        )
        arjun_urls = set()
        for line in result.stdout.splitlines():
            url = line.strip()
            if "?" in url:
                arjun_urls.add(url)
        return list(arjun_urls)

    except subprocess.CalledProcessError as e:
        print(f"[!] Arjun error: {e}")
        return []


def discover_all_parameters(domain):
    paramspider_urls = run_paramspider(domain)
    arjun_urls = run_arjun(paramspider_urls)

    all_urls = set(paramspider_urls + arjun_urls)

    print(f"[✓] Total URLs with parameters collected: {len(all_urls)}")

    return extract_parameters(list(all_urls))
