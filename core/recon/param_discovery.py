import asyncio
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Tuple

async def extract_parameters(urls: List[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    param_names: Set[str] = set()
    param_map: Dict[str, List[str]] = {}

    # Process URLs in parallel
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(*[
            loop.run_in_executor(executor, _process_single_url, url)
            for url in urls
        ])

    for params, url in results:
        for param in params:
            param_names.add(param)
            param_map.setdefault(param, []).append(url)

    return param_names, param_map

def _process_single_url(url: str) -> Tuple[Set[str], str]:
    parsed = urlparse(url)
    params = set(parse_qs(parsed.query).keys())
    return params, url

async def run_paramspider(domain: str) -> List[str]:
    print(f"[+] Running ParamSpider on: {domain}")

    paramspider_dir = os.environ.get("PARAMSPIDER_PATH", "/opt/ParamSpider")
    env = {**os.environ, "PYTHONPATH": paramspider_dir}

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-m", "paramspider.main", "-d", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=paramspider_dir,
            env=env
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(f"[!] ParamSpider error: {stderr.decode().strip()}")
            return []

        urls = set()
        for line in stdout.decode().splitlines():
            if "?" in (url := line.strip()):
                urls.add(url)
        return list(urls)

    except Exception as e:
        print(f"[!] ParamSpider execution failed: {e}")
        return []

async def run_arjun(urls: List[str]) -> List[str]:
    print(f"[+] Running Arjun on collected URLs...")

    input_data = "\n".join(urls)
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "arjun/arjun.py", "--stdin", "--get", "--threads", "10",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate(input=input_data.encode())

        if proc.returncode != 0:
            print(f"[!] Arjun error: {stderr.decode().strip()}")
            return []

        arjun_urls = set()
        for line in stdout.decode().splitlines():
            if "?" in (url := line.strip()):
                arjun_urls.add(url)
        return list(arjun_urls)

    except Exception as e:
        print(f"[!] Arjun execution failed: {e}")
        return []

async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    # Run tools concurrently
    paramspider_urls, arjun_urls = await asyncio.gather(
        run_paramspider(domain),
        run_arjun([])  # Empty initial run to warm up
    )
    
    # Second Arjun run with actual data
    arjun_urls = await run_arjun(paramspider_urls)

    all_urls = set(paramspider_urls + arjun_urls)
    print(f"[✓] Total URLs with parameters collected: {len(all_urls)}")

    return await extract_parameters(list(all_urls))

# Sync wrapper for compatibility with existing Flask app
def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))

# Maintain original interface
discover_all_parameters = discover_all_parameters_sync
