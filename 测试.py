fxbl = "fuck_you = aa"
sb = []
if " = " in fxbl:
    print(fxbl)
    import jieba
    yslist = jieba.lcut(fxbl)
    print(yslist)
    dyfcdw = yslist.index("=")
    dyfcdw = dyfcdw - 2
    print(dyfcdw)
    blm = yslist[dyfcdw]
    print(blm)
    sb.append(blm)