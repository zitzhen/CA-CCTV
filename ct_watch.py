domains = open("domains.txt", mode='r',encoding="utf-8")
# Filter comment lines and empty lines
for line in domains:
    line = line.strip()
    if not line:
       continue
    if line.startswith("#"):
        continue
    print(line)
domains.close()