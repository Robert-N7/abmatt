#!/usr/bin/python
import re
f = open("tmp.txt", "r")
lines = f.readlines()
f.close()
s = ""
f = open("tmp2.txt", "w")
for line in lines:
    m = re.search("\d+", line)
    if m:
        print("Found match")
    line = re.sub("(\d+)", lambda m: str(int(m[0]) - 32), line)
    # print(line)
    f.write(line)
