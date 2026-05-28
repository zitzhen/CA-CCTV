domain_list = []
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