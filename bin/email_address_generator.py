import sys
import csv

rdr = csv.reader(sys.stdin)
lst = set()
for x in rdr:
    v = x[0].strip()
    try:
        a, b = v.split( )
        lst.add(f"{a[0]}.{b}@f5.com")
    except ValueError:
        pass

for x in lst:
    print(x)

