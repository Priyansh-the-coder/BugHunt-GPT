import asyncio
import os
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Tuple
import glob
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
    print(f"[+] Running ParamSpider on: {domain}")

    paramspider_dir = "/opt/ParamSpider"
    main_script = os.path.join(paramspider_dir,"main.py")
     # Diagnostic: print entire tree of /opt/ParamSpider
    debug_tree = []
    for root, dirs, files in os.walk(paramspider_dir):
        for name in files:
            debug_tree.append(os.path.join(root, name))

    raise FileNotFoundError(
        f"[!] ParamSpider main script not found.\n"
        f"[i] Scanned path: {paramspider_dir}\n"
        f"[i] Files found:\n" + "\n".join(debug_tree)
    )
    if not os.path.exists(main_script):
        raise FileNotFoundError(f"[!] ParamSpider script not found at: {main_script}")

    env = {**os.environ}

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3",main_script, "-d", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=paramspider_dir,
            env=env
        )
        stdout, stderr = await proc.communicate()

        stdout_decoded = stdout.decode().strip()
        stderr_decoded = stderr.decode().strip()

        if proc.returncode != 0:
            raise RuntimeError(f"[!] ParamSpider failed (code {proc.returncode}): {stderr_decoded}")

        urls = set()
        for line in stdout_decoded.splitlines():
            if "?" in (url := line.strip()):
                urls.add(url)

        print(f"[✓] ParamSpider found {len(urls)} URLs with parameters.")
        return list(urls)

    except Exception as e:
        raise RuntimeError(f"[!] ParamSpider exception: {e}")


# ---------------- Sync Wrapper ----------------

def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))

async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    urls = await run_paramspider(domain)
    return await extract_parameters(urls)

# ---------------- Flask Endpoint ----------------




