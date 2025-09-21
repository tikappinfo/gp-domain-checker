import random, time
from typing import Dict
import os, requests

DOH_URL = "https://dns.google/resolve"
TIME_BETWEEN = (0.5, 1.1)

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

def doh_query(name: str, rtype: str = "A") -> Dict:
    params = {"name": name, "type": rtype}
    resp = requests.get(DOH_URL, params=params, headers={"User-Agent": random.choice(UA)}, timeout=15)
    resp.raise_for_status()
    time.sleep(random.uniform(*TIME_BETWEEN))
    return resp.json()

def availability(domain: str) -> str:
    try:
        j = doh_query(domain, "A")
        status = j.get("Status")
        if status == 3:
            return "available"
        if j.get("Answer"):
            return "taken"
        return "taken"
    except Exception:
        return "unknown"

def check_pair(label: str) -> Dict[str, str]:
    com = f"{label}.com"
    net = f"{label}.net"
    return {"dotcom_status": availability(com), "dotnet_status": availability(net)}
import requests

DNS_GOOGLE = "https://dns.google/resolve"


def doh_query(name: str, qtype: str = "A"):
    try:
        insecure = os.environ.get("REQUESTS_INSECURE", "0") == "1"
        r = requests.get(DNS_GOOGLE, params={"name": name, "type": qtype}, timeout=15, verify=False if insecure else True)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def availability(domain: str) -> str:
    data = doh_query(domain, "A")
    if not data:
        return "unknown"
    status = data.get("Status")
    if status == 3:  # NXDOMAIN
        return "available"
    # If there's an Answer or an authoritative SOA in Authority, treat as taken
    if data.get("Answer") or data.get("Authority"):
        return "taken"
    return "unknown"


def check_pair(label: str):
    dotcom = f"{label}.com"
    dotnet = f"{label}.net"
    return {
        "dotcom_status": availability(dotcom),
        "dotnet_status": availability(dotnet),
    }
