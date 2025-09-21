import random, re, time
from typing import List, Dict, Tuple, Set
import requests
import certifi
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

HEADERS_BASE = lambda: {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept-Language": "en-US,en;q=0.9",
}

DETAILS_URL = "https://play.google.com/store/apps/details?id={app_id}"
TIME_BETWEEN = (1.0, 2.2)

SEED_URLS = [
    "https://play.google.com/store/apps/category/COMMUNICATION",
    "https://play.google.com/store/apps/category/PRODUCTIVITY",
    "https://play.google.com/store/apps/category/TOOLS",
    "https://play.google.com/store/apps/category/VIDEO_PLAYERS",
    "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE",
    "https://play.google.com/store/apps/dev?id=7083182635971239206",
    "https://play.google.com/store/apps/developer?id=WireGuard+Development+Team",
    "https://play.google.com/store/apps/developer?id=Nextcloud",
    "https://play.google.com/store/apps/dev?id=8483587772816822023",
    "https://play.google.com/store/apps/dev?id=7543681500912687681",
    "https://play.google.com/store/apps/dev?id=4758894585905287660",
    "https://play.google.com/store/apps/dev?id=9116215767541857492",
    "https://play.google.com/store/apps/developer?id=Bitwarden+Inc.",
    "https://play.google.com/store/apps/developer?id=Collabora+Productivity+Limited",
    "https://play.google.com/store/apps/developer?id=Vivaldi+Technologies",
    "https://play.google.com/store/apps/developer?id=APK+Mirror",
]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def fetch(url: str) -> str:
    resp = requests.get(url, headers=HEADERS_BASE(), timeout=20)
    resp.raise_for_status()
    time.sleep(random.uniform(*TIME_BETWEEN))
    return resp.text

def extract_app_ids_from_page(html: str) -> Set[str]:
    ids = set(re.findall(r"/store/apps/details\?id=([a-zA-Z0-9._\-]+)", html))
    return ids

def parse_title_and_installs(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    og_title = soup.find("meta", {"property": "og:title"})
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    text = soup.get_text(" ", strip=True)
    m = re.search(r"(\d+(?:\.\d+)?)\s*([KM])\+\s*Downloads", text, re.I)
    installs = ""
    if m:
        num, unit = m.group(1), m.group(2).upper()
        installs = f"{num}{unit}+"
    else:
        m2 = re.search(r"(\d+(?:\.\d+)?)([KM])\+Downloads", text, re.I)
        if m2:
            installs = f"{m2.group(1)}{m2.group(2).upper()}+"
    return title, installs

def in_range_1_to_10m(installs: str) -> bool:
    if not installs:
        return False
    m = re.match(r"(\d+(?:\.\d+)?)([KM])\+$", installs)
    if not m:
        return False
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "K":
        return False
    return 1.0 <= num <= 10.0

def crawl(seed_urls: List[str], max_items: int) -> List[Dict]:
    seen_ids: Set[str] = set()
    results: List[Dict] = []

    for url in seed_urls:
        try:
            html = fetch(url)
            ids = extract_app_ids_from_page(html)
            seen_ids.update(ids)
        except Exception:
            continue
        if len(seen_ids) >= max_items * 3:
            break

    for app_id in list(seen_ids):
        if len(results) >= max_items:
            break
        try:
            html = fetch(DETAILS_URL.format(app_id=app_id))
            title, installs = parse_title_and_installs(html)
            if title and in_range_1_to_10m(installs):
                results.append({"app_id": app_id, "title": title, "installs": installs})
        except Exception:
            continue

    if len(results) < max_items:
        more_urls = set()
        for url in seed_urls:
            try:
                html = fetch(url)
                more_urls.update(re.findall(r"https://play\.google\.com/store/apps/collection/cluster\?[^\"']+", html))
            except Exception:
                pass
        for url in list(more_urls):
            if len(results) >= max_items:
                break
            try:
                html = fetch(url)
                ids = extract_app_ids_from_page(html)
                for app_id in ids:
                    if len(results) >= max_items:
                        break
                    if app_id in {r["app_id"] for r in results}:
                        continue
                    try:
                        dhtml = fetch(DETAILS_URL.format(app_id=app_id))
                        title, installs = parse_title_and_installs(dhtml)
                        if title and in_range_1_to_10m(installs):
                            results.append({"app_id": app_id, "title": title, "installs": installs})
                    except Exception:
                        continue
            except Exception:
                continue

    return results
import random
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

HEADERS_LIST = [
    {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    for ua in [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
]

@retry(reraise=True, stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3), retry=retry_if_exception_type(Exception))
def fetch(url: str, timeout: int = 12) -> str:
    headers = random.choice(HEADERS_LIST)
    try:
        r = requests.get(url, headers=headers, timeout=timeout, verify=certifi.where())
        if r.status_code >= 500:
            raise RuntimeError(f"Server error {r.status_code}")
        r.raise_for_status()
        time.sleep(random.uniform(0.15, 0.35))
        return r.text
    except Exception:
        # Fallback via text proxy to bypass network/SSL blocks
        try:
            inner = url
            if inner.startswith("https://"):
                inner = inner[len("https://"):]
            elif inner.startswith("http://"):
                inner = inner[len("http://"):]
            proxy_url = f"https://r.jina.ai/http://{inner}"
            r2 = requests.get(proxy_url, headers={"User-Agent": headers["User-Agent"]}, timeout=timeout)
            r2.raise_for_status()
            time.sleep(random.uniform(0.1, 0.25))
            return r2.text
        except Exception as e:
            raise e

APP_ID_RE = re.compile(r"/store/apps/details\?id=([a-zA-Z0-9_\.\-]+)")


def extract_app_ids_from_page(html: str) -> List[str]:
    ids = set(APP_ID_RE.findall(html))
    return list(ids)


def parse_title_and_installs(html: str) -> Optional[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    def clean_title(raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        s = raw.strip()
        suffix = " - Apps on Google Play"
        if s.endswith(suffix):
            s = s[: -len(suffix)]
        return s

    title = None
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        title = clean_title(og["content"])  # prefer English meta
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = clean_title(h1.get_text(strip=True))

    if not title:
        return None

    text = soup.get_text(" ", strip=True)
    m = re.search(r"([0-9][0-9,\.]*\s*[KMB]\+?|[0-9][0-9,\.]*\+)\s*downloads", text, re.IGNORECASE)
    installs = m.group(1).replace(" ", "") + "+downloads" if m else ""

    return {"title": title, "installs": installs}


def in_range_1_to_10m(installs: str) -> bool:
    s = installs.lower().replace(",", "")
    if not s:
        return False
    if "k+" in s:
        return False
    # Accept numeric forms like 1,000,000+ or 1M+
    if "m+" in s:
        try:
            val = float(s.split("m+")[0])
            return 1 <= val <= 10
        except Exception:
            return False
    if s.endswith("+downloads"):
        s = s[:-10]
    if s.endswith("+"):
        s = s[:-1]
    try:
        n = int(s)
        return 1_000_000 <= n <= 10_000_000
    except Exception:
        return False


SEED_URLS: List[str] = [
    # Broad category coverage (US/English)
    "https://play.google.com/store/apps/category/TOOLS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/PRODUCTIVITY?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/COMMUNICATION?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/MAPS_AND_NAVIGATION?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/EDUCATION?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/HEALTH_AND_FITNESS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/FINANCE?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/ENTERTAINMENT?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/SOCIAL?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/PHOTOGRAPHY?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/VIDEO_PLAYERS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/MUSIC_AND_AUDIO?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/NEWS_AND_MAGAZINES?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/SHOPPING?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/SPORTS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/TRAVEL_AND_LOCAL?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/LIFESTYLE?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/BUSINESS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/PERSONALIZATION?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/FOOD_AND_DRINK?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/HOUSE_AND_HOME?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/AUTO_AND_VEHICLES?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/PARENTING?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/DATING?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/EVENTS?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/ART_AND_DESIGN?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/BEAUTY?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/MEDICAL?hl=en_US&gl=US",
    "https://play.google.com/store/apps/category/WEATHER?hl=en_US&gl=US",
    # A few developer pages with many utilities/open-source apps
    "https://play.google.com/store/apps/dev?id=6672484314740823363&hl=en_US&gl=US",  # Mozilla
    "https://play.google.com/store/apps/dev?id=9035793846880984416&hl=en_US&gl=US",  # KDE
    "https://play.google.com/store/apps/dev?id=8894090302098729471&hl=en_US&gl=US",  # Nextcloud
    "https://play.google.com/store/apps/dev?id=5304367239072397594&hl=en_US&gl=US",  # Bitwarden
]

# Expand coverage via A–Z and 0–9 search seeds (US/English)
SEED_URLS += [
    f"https://play.google.com/store/search?q={ch}&c=apps&hl=en&gl=US"
    for ch in list("abcdefghijklmnopqrstuvwxyz0123456789")
]


def crawl(seed_urls: List[str], max_items: int = 500) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    seen_ids = set()
    # Phase 1: scan seed pages for app IDs
    for url in seed_urls:
        try:
            html = fetch(url)
        except Exception:
            continue
        for app_id in extract_app_ids_from_page(html):
            if app_id not in seen_ids:
                seen_ids.add(app_id)
    try:
        print(f"Seeds scanned. Collected {len(seen_ids)} unique app IDs.")
    except Exception:
        pass

    # Phase 2: visit app detail pages and collect those within range
    detail_base = "https://play.google.com/store/apps/details?hl=en&gl=US&id="

    id_list = list(seen_ids)
    random.shuffle(id_list)
    examined = 0
    max_examine = max_items * 12  # examine more detail pages to reliably hit target

    for app_id in id_list: 
        if len(found) >= max_items:
            break
        if examined >= max_examine:
            break
        try:
            html = fetch(detail_base + app_id)
        except Exception:
            continue
        parsed = parse_title_and_installs(html)
        if not parsed:
            examined += 1
            continue
        if in_range_1_to_10m(parsed["installs"]):
            found.append({"app_id": app_id, "title": parsed["title"], "installs": parsed["installs"]})
        examined += 1
        if examined % 50 == 0:
            try:
                print(f"Progress: examined {examined}/{max_examine}, found {len(found)} candidates.")
            except Exception:
                pass

    return found
