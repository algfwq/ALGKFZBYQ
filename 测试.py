import linecache
from tkinter import Text, Menu
from tkinter.constants import END, DISABLED

import pyperclip as pyperclip
from ttkbootstrap import Window

self = Window()
self.text = Text(self)
self.text.pack()


def bc():
    open("sb.txt", "w+").write(self.text.get(float(1), END))


# 代码补全=====================
def bqzt(event):
    bc()
    # 创建函数列表
    dmlist = ["print", "text",'ppp']
    # 定位内容
    self.gbw = self.text.index("insert")

    def numzs(num):
        '''
        浮点数字整数、小数分离【将数字转化为字符串处理】
        '''
        zs, xs = str(num).split('.')
        return zs

    def numxs(num):
        '''
        浮点数字整数、小数分离【将数字转化为字符串处理】
        '''
        zs, xs = str(num).split('.')
        return xs

    linenum = numzs(self.gbw)
    linenum2 = int(linenum)
    lie = numxs(self.gbw)
    lie2 = int(lie)
    bc()
    text = linecache.getline("sb.txt", linenum2)
    ftext = text[0:lie2]
    print(ftext)
    # 利用分词，获取用户输入的那半个函数
    import jieba
    feilist = jieba.lcut(ftext)

    def power(n):
        jian = n + n
        far = n - jian
        return far

    a = 0
    while True:
        try:
            if feilist[power(a)] == "\n":
                a = a + 1
            else:
                print(feilist[power(a)])
                bandm = feilist[power(a)]
                break
        except IndexError:
            pass
    # 得到候选函数列表
    # 候选列表
    hx = []
    lennum = len(bandm)
    for i in dmlist:
        db = i[0:lennum]
        if db == i:
            pass
        elif db == bandm:
            hx.append(i)
    if hx == []:
        hx.append("无建议")
    print(hx)

    # 插入组件
    def cr(bandm, xzdm):  # bandm用户输入的那一半代码，xzdm用户选择的代码
        '''bancd = len(bandm)
        xzcd = len(xzdm)
        bqdm = xzdm[bancd:xzcd]
        pyperclip.copy(bqdm)'''
        pyperclip.copy(xzdm)

        def zt(event=None):
            global root
            self.text.event_generate('<<Paste>>')

        zt()

    # 补全弹窗
    self.mnu = Menu()
    if hx == ["无建议"]:
        self.mnu.add_command(label="无建议", state=DISABLED)
    else:
        for i in hx:
            def cmd():
                cr(feilist[power(a)], i.replace(feilist[power(a)], ''))

            self.mnu.add_command(label=i, command=cmd)
    self.mnu.post(self.winfo_x(), self.winfo_y())


self.text.bind("<Alt_L>", bqzt)
# 代码补全底======================
self.mainloop()