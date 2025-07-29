import asyncio
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Tuple

# ---------------- Core Functions ----------------

def _process_single_url(url: str) -> Tuple[Set[str], str]:
    parsed = urlparse(url)
    params = set(parse_qs(parsed.query).keys())
    return params, url

async def extract_parameters(urls: List[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    param_names: Set[str] = set()
    param_map: Dict[str, List[str]] = {}

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

async def run_paramspider(domain: str) -> List[str]:
    paramspider_main = "/opt/ParamSpider/paramspider/main.py"

    if not os.path.exists(paramspider_main):
        raise FileNotFoundError(f"ParamSpider main.py not found at {paramspider_main}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", paramspider_main, "-d", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/opt/ParamSpider"
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"ParamSpider failed: {stderr.decode().strip()}")

        urls = set()
        for line in stdout.decode().splitlines():
            if "?" in line:
                urls.add(line.strip())

        return list(urls)

    except Exception as e:
        raise RuntimeError(f"ParamSpider execution error: {e}")

# ---------------- Sync Wrapper ----------------

def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))

async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    urls = await run_paramspider(domain)
    return await extract_parameters(urls)

# ---------------- Flask Endpoint ----------------




