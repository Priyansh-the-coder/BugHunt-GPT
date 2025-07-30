import asyncio
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Tuple
import glob
import subprocess
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
    env = os.environ.copy()
    env["PYTHONPATH"] = "/opt/ParamSpider"
    paramspider_dir = "/opt/ParamSpider/paramspider"
    main_script = os.path.join(paramspider_dir, "main.py")

    if not os.path.exists(main_script):
        raise FileNotFoundError(f"[!] ParamSpider script not found at: {main_script}")

    try:
        proc = await asyncio.create_subprocess_exec(
    "python3", "-m", "paramspider.main", "-d", domain,
    cwd="/opt/ParamSpider",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env
)
        stdout_bytes, stderr_bytes = await proc.communicate()

        stdout = stdout_bytes.decode("utf-8", errors="ignore")
        stderr = stderr_bytes.decode("utf-8", errors="ignore")

        # 🧪 Send both stdout and stderr back to API caller if error occurs
        if proc.returncode != 0:
            raise RuntimeError(
                f"[!] ParamSpider failed (code {proc.returncode})\n[STDOUT]\n{stdout}\n[STDERR]\n{stderr}"
            )

        urls = set()
        for line in stdout.splitlines():
            if "?" in (url := line.strip()):
                urls.add(url)

        return list(urls)

    except Exception as e:
        raise RuntimeError(f"[!] ParamSpider exception: {str(e)}")



# ---------------- Sync Wrapper ----------------

def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))

async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    urls = await run_paramspider(domain)
    return await extract_parameters(urls)

# ---------------- Flask Endpoint ----------------




