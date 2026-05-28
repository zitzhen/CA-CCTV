domain_list = []

with open("domains.txt", mode="r", encoding="utf-8") as domains:
    for line in domains:
        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        domain_list.append(line)

print(domain_list)