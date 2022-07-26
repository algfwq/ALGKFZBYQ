a = '''sb
sb
sb
sb
aa'''

import linecache
b = linecache.getline(a, 5)
print(b)