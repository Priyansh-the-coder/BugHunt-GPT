import asyncio
import os
import sys
import logging
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


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


def _process_single_url(url: str) -> Tuple[Set[str], str]:
    parsed = urlparse(url)
    params = set(parse_qs(parsed.query).keys())
    return params, url


async def run_paramspider(domain: str) -> List[str]:
    logger.info(f"[+] Running ParamSpider on: {domain}")

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

        urls = set()
        async for line in proc.stdout:
            decoded = line.decode().strip()
            logger.info(f"[ParamSpider] {decoded}")
            sys.stdout.flush()
            if "?" in decoded:
                urls.add(decoded)

        stderr = await proc.stderr.read()
        if stderr:
            logger.error(f"[ParamSpider STDERR] {stderr.decode().strip()}")
            sys.stdout.flush()

        return list(urls)

    except Exception as e:
        logger.exception(f"[!] ParamSpider execution failed: {e}")
        sys.stdout.flush()
        return []


async def run_arjun(urls: List[str]) -> List[str]:
    logger.info(f"[+] Running Arjun on {len(urls)} URLs...")

    if not urls:
        return []

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
            logger.error(f"[Arjun STDERR] {stderr.decode().strip()}")
            sys.stdout.flush()
            return []

        arjun_urls = set()
        for line in stdout.decode().splitlines():
            line = line.strip()
            logger.info(f"[Arjun] {line}")
            sys.stdout.flush()
            if "?" in line:
                arjun_urls.add(line)

        return list(arjun_urls)

    except Exception as e:
        logger.exception(f"[!] Arjun execution failed: {e}")
        sys.stdout.flush()
        return []


async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    logger.info(f"[*] Starting parameter discovery for: {domain}")

    paramspider_urls, _ = await asyncio.gather(
        run_paramspider(domain),
        run_arjun([])  # Warm-up call; discarded
    )

    arjun_urls = await run_arjun(paramspider_urls)
    all_urls = set(paramspider_urls + arjun_urls)

    logger.info(f"[✓] Total URLs with parameters collected: {len(all_urls)}")
    sys.stdout.flush()

    return await extract_parameters(list(all_urls))


def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))


# Sync compatibility
discover_all_parameters = discover_all_parameters_sync
