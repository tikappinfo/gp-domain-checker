import requests

LABELS = [
    'bitwardenpasswordmanager','kdeconnect','nextcloud','organicmapshikebikedrive',
    'osmandmapsgpsoffline','torbrowser','solidexplorerfilemanager','keepass2androidpasswordsafe',
    'apkmirrorinstallerofficial','anysoftkeyboard','kiwix','wireguard'
]

URL = 'https://dns.google/resolve'


def status(domain: str) -> str:
    try:
        r = requests.get(URL, params={'name': domain, 'type': 'A'}, timeout=20)
        j = r.json(); s = j.get('Status')
        if s == 3:
            return 'available'
        if j.get('Answer') or j.get('Authority'):
            return 'taken'
        return 'unknown'
    except Exception:
        return 'unknown'


def main():
    print('label,dotcom,dotnet')
    for lb in LABELS:
        dc = status(lb + '.com')
        dn = status(lb + '.net')
        print(f"{lb},{dc},{dn}")


if __name__ == '__main__':
    main()
