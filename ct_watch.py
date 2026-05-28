import requests
domain_list = []

def fetch_certs(domain: str) -> list[dict]:
    url = "https://crt.sh/"
    params = {
        "q": f"%.{domain}",
        "output": "json",
        "deduplicate": "Y",
    }

    headers = {
        "User-Agent": "ct-watch/1.0 (+https://github.com/Iamliuxiaozhen/CA_CCTV)"
    }

    last_error = None

    for attempt in range(1, 4):
        try:
            print(f"[*] Query crt.sh attempt {attempt}/3...")
            r = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=(10, 90),
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"[!] crt.sh failed: {e}")
            time.sleep(5 * attempt)

    raise RuntimeError(f"crt.sh query failed after retries: {last_error}")

def fetchdomains():
    with open("domains.txt", mode="r", encoding="utf-8") as domains:
        for line in domains:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            domain_list.append(line)

    print("Domains to be scanned:")
    print(domain_list)

if (__name__ =="__main__"):
    fetchdomains()