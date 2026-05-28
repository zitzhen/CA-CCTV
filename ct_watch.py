domain_list = []
domains = open("domains.txt", mode='r',encoding="utf-8")
# Filter comment lines and empty lines
for line in domains:
    line = line.strip()
    if not line:
       continue
    if line.startswith("#"):
        continue
    domain_list.append(line)
    print(domain_list)
domains.close()