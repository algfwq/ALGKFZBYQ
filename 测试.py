import jieba
feilist = jieba.lcut("print\n\n\n\n")
def power(n):
    jian = n + n
    far = n - jian
    return far
a = 2
while True:
    if feilist[power(a)] == "\n":
        a = a + 1
    else:
        print(feilist[power(a)])
        break