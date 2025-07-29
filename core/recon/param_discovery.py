import asyncio
import os
from urllib.parse import urlparse, parse_qs
from typing import Set, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

def _process_single_url(url: str) -> Tuple[Set[str], str]:
    parsed = urlparse(url)
    params = set(parse_qs(parsed.query).keys())
    return params, url

async def extract_parameters(urls: List[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    param_names = set()
    param_map = {}

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

    paramspider_main = "/opt/ParamSpider/paramspider/main.py"

    if not os.path.exists(paramspider_main):
        raise FileNotFoundError(f"[!] ParamSpider main.py not found at {paramspider_main}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", paramspider_main, "-d", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/opt/ParamSpider"
        )
        stdout, stderr = await proc.communicate()

        stderr_output = stderr.decode().strip()
        if proc.returncode != 0:
            raise RuntimeError(f"[!] ParamSpider exited with code {proc.returncode}:\n{stderr_output or '(no stderr output)'}")

        urls = set()
        for line in stdout.decode().splitlines():
            if "?" in (url := line.strip()):
                urls.add(url)

        print(f"[+] ParamSpider found {len(urls)} URLs")
        return list(urls)

    except Exception as e:
        raise RuntimeError(f"[!] ParamSpider execution failed: {e}")


async def run_arjun(urls: List[str]) -> List[str]:
    print(f"[+] Running Arjun on collected URLs...")
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
            print(f"[!] Arjun error: {stderr.decode().strip()}")
            logger.error(f"[Arjun STDERR] {stderr.decode().strip()}")
            sys.stdout.flush()
            return []

        arjun_urls = set()
        for line in stdout.decode().splitlines():
            if "?" in (url := line.strip()):
                arjun_urls.add(url)
            line = line.strip()
            logger.info(f"[Arjun] {line}")
            sys.stdout.flush()
            if "?" in line:
                arjun_urls.add(line)

        return list(arjun_urls)

    except Exception as e:
        print(f"[!] Arjun execution failed: {e}")
        logger.exception(f"[!] Arjun execution failed: {e}")
        sys.stdout.flush()
        return []

async def discover_all_parameters(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    # Remove protocol prefix if exists
    domain = domain.replace("http://", "").replace("https://", "").strip("/")

    paramspider_urls = await run_paramspider(domain)
    if not paramspider_urls:
        raise RuntimeError(f"ParamSpider failed for domain: {domain}")

    arjun_urls = await run_arjun(paramspider_urls)

    all_urls = set(paramspider_urls + arjun_urls)
    return await extract_parameters(list(all_urls))


def discover_all_parameters_sync(domain: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    return asyncio.run(discover_all_parameters(domain))
