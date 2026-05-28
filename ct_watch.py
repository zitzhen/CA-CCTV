domains = open("domains.txt", mode='r',encoding="utf-8")
# Filter comment lines
for line in domains:
    if line.startswith("#"):
        continue
    print(line)
domains.close()