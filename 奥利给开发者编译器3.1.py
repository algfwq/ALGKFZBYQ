#导库
from tkinter import *
import os
import pyperclip
import ttkbootstrap as t
from tkinter.messagebox import *

#闪屏动画
#import loading_window

#代码高亮（头）
try:  # 调用idle进行高亮
    from idlelib.colorizer import ColorDelegator
    from idlelib.percolator import Percolator
    from idlelib import autocomplete
except (ImportError,ModuleNotFoundError):  # 可能未安装IDLE
    ColorDelegator = Percolator = None
    autocomplete = None
#代码高亮（头）

#高分辨率适配
import ctypes
#告诉操作系统使用程序自身的dpi适配
ctypes.windll.shcore.SetProcessDpiAwareness(1)
#获取屏幕的缩放因子
ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)

#函数区
#代码替换=======================
import os
import re

from ttkbootstrap import *
from tkinter import Frame, Label
from tkinter.constants import *
import ttkbootstrap as ttk
from tkPlus import messagebox as msgbox


def handle(err, parent=None):
    # 用于处理错误
    # showinfo()中,parent参数指定消息框的父窗口
    msgbox.showinfo("错误", type(err).__name__ + ': ' + str(err), parent=parent)


def to_escape_str(byte):
    # 将字节(bytes)转换为转义字符串
    str = '';
    length = 1024
    for i in range(0, len(byte), length):
        str += repr(byte[i: i + length])[2:-1]
        str += '\n'
    return str


def to_bytes(escape_str):
    # 将转义字符串转换为字节
    # -*****- 1.2.5版更新: 忽略二进制模式中文字的换行符
    escape_str = escape_str.replace('\n', '')
    escape_str = escape_str.replace('"""', '\\"\\"\\"')  # 避免引号导致的SyntaxError
    escape_str = escape_str.replace("'''", "\\'\\'\\'")
    try:
        return eval('b"""' + escape_str + '"""')
    except SyntaxError:
        return eval("b'''" + escape_str + "'''")


def bell_(*args):
    msgbox.showwarning("啥也没有欸...", "如题")


class SearchDialog(Toplevel):
    # 查找对话框
    def __init__(self, master, text):
        self.master = master
        self.text = text
        self.coding = self.master.coding.get()

    def init_window(self, title="查找"):
        Toplevel.__init__(self, self.master)
        self.title(title)
        self.attributes("-toolwindow", True)
        self.attributes("-topmost", True)
        # 当父窗口隐藏后，窗口也跟随父窗口隐藏
        #self.transient(self.master)
        #self.wm_protocol("WM_DELETE_WINDOW", self.onquit)

    def show(self):
        self.init_window()
        frame = Frame(self)
        ttk.Button(frame, text="查找下一个", command=self.search).pack()
        ttk.Button(frame, text="退出", command=self.onquit).pack()
        frame.pack(side=RIGHT, fill=Y)
        inputbox = Frame(self)
        Label(inputbox, text="查找内容:").pack(side=LEFT)
        self.keyword = StringVar(self.master)
        keyword = ttk.Entry(inputbox, textvariable=self.keyword)
        keyword.pack(side=LEFT, expand=True, fill=X)
        keyword.bind("<Key-Return>", self.search)
        keyword.focus_force()
        inputbox.pack(fill=X)
        options = Frame(self)
        self.create_options(options)
        options.pack(fill=X)

    def create_options(self, master):
        Label(master, text="选项: ").pack(side=LEFT)
        self.use_regexpr = IntVar(self.master)
        ttk.Checkbutton(master, text="使用正则表达式", variable=self.use_regexpr) \
            .pack(side=LEFT)
        self.match_case = IntVar(self.master)
        ttk.Checkbutton(master, text="区分大小写", variable=self.match_case) \
            .pack(side=LEFT)
        self.use_escape_char = IntVar(self.master)
        self.use_escape_char.set(self.master.isbinary)
        ttk.Checkbutton(master, text="使用转义字符", variable=self.use_escape_char) \
            .pack(side=LEFT)

    def search(self, event=None, mark=True, bell=True):
        text = self.text
        key = self.keyword.get()
        if not key: return
        # 验证用户输入是否正常
        if self.use_escape_char.get():
            try:
                key = str(to_bytes(key), encoding=self.coding)
            except Exception as err:
                handle(err, parent=self)
                return
        if self.use_regexpr.get():
            try:
                re.compile(key)
            except re.error as err:
                handle(err, parent=self)
                return
        # 默认从当前光标位置开始查找
        pos = text.search(key, INSERT, 'end-1c',  # end-1c:忽略末尾换行符
                          regexp=self.use_regexpr.get(),
                          nocase=not self.match_case.get())
        if not pos:
            # 尝试从开头循环查找
            pos = text.search(key, '1.0', 'end-1c',
                              regexp=self.use_regexpr.get(),
                              nocase=not self.match_case.get())
        if pos:
            if self.use_regexpr.get():  # 获取正则表达式匹配的字符串长度
                text_after = text.get(pos, END)
                flag = re.IGNORECASE if not self.match_case.get() else 0
                length = re.match(key, text_after, flag).span()[1]
            else:
                length = len(key)
            newpos = "%s+%dc" % (pos, length)
            text.mark_set(INSERT, newpos)
            if mark: self.mark_text(pos, newpos)
            return pos, newpos
        elif bell:  # 未找到,返回None
            bell_(widget=self)

    def findnext(self, cursor_pos='end', mark=True, bell=True):
        # cursor_pos:标记文本后将光标放在找到文本开头还是末尾
        # 因为search()默认从当前光标位置开始查找
        # end 用于查找下一个操作, start 用于替换操作
        result = self.search(mark=mark, bell=bell)
        if not result: return
        if cursor_pos == 'end':
            self.text.mark_set('insert', result[1])
        elif cursor_pos == 'start':
            self.text.mark_set('insert', result[0])
        return result

    def mark_text(self, start_pos, end_pos):
        text = self.text
        text.tag_remove("sel", "1.0", END)  # 移除旧的tag
        # 已知问题: 代码高亮显示时, 无法突出显示找到的文字
        text.tag_add("sel", start_pos, end_pos)  # 添加新的tag
        lines = text.get('1.0', END)[:-1].count(os.linesep) + 1
        lineno = int(start_pos.split('.')[0])
        # 滚动文本框, 使被找到的内容显示 ( 由于只判断行数, 已知有bug); 另外, text['height']不会随文本框缩放而变化
        text.yview('moveto', str((lineno - text['height']) / lines))
        text.focus_force()
        self.master.update_status()

    def onquit(self):
        self.withdraw()


class ReplaceDialog(SearchDialog):
    # 替换对话框
    def show(self):
        self.init_window(title="替换")
        frame = Frame(self)
        t.Button(frame, text="查找下一个", command=self._findnext,bootstyle=sjanys()).pack()
        t.Button(frame, text="替换", command=self.replace,bootstyle=sjanys()).pack()
        t.Button(frame, text="全部替换", command=self.replace_all,bootstyle=sjanys()).pack()
        t.Button(frame, text="退出", command=self.onquit,bootstyle=sjanys()).pack()
        frame.pack(side=RIGHT, fill=Y)

        inputbox = Frame(self)
        Label(inputbox, text="查找内容:").pack(side=LEFT)
        self.keyword = StringVar(self.master)
        keyword = ttk.Entry(inputbox, textvariable=self.keyword,bootstyle=sjys())
        keyword.pack(side=LEFT, expand=True, fill=X)
        keyword.focus_force()
        inputbox.pack(fill=X)

        replace = Frame(self)
        Label(replace, text="替换为:  ").pack(side=LEFT)
        self.text_to_replace = StringVar(self.master)
        replace_text = ttk.Entry(replace, textvariable=self.text_to_replace,bootstyle=sjys())
        replace_text.pack(side=LEFT, expand=True, fill=X)
        replace_text.bind("<Key-Return>", self.replace)
        replace.pack(fill=X)

        options = Frame(self)
        self.create_options(options)
        options.pack(fill=X)

    def _findnext(self):  # 仅用于"查找下一个"按钮功能
        text = self.text
        sel_range = text.tag_ranges('sel')  # 获得选区的起点和终点
        if sel_range:
            selectarea = sel_range[0].string, sel_range[1].string
            result = self.findnext('start')
            if result is None: return
            if result[0] == selectarea[0]:  # 若仍停留在原位置
                text.mark_set('insert', result[1])  # 从选区终点继续查找
                self.findnext('start')
        else:
            self.findnext('start')

    def replace(self, bell=True, mark=True):
        text = self.text
        result = self.search(mark=False, bell=bell)
        if not result: return  # 标志已无文本可替换
        # self.master.text_change()
        pos, newpos = result
        newtext = self.text_to_replace.get()
        try:
            if self.use_escape_char.get():
                newtext = to_bytes(newtext).decode(self.master.coding.get())
            if self.use_regexpr.get():
                old = text.get(pos, newpos)
                newtext = re.sub(self.keyword.get(), newtext, old)
        except Exception as err:
            handle(err, parent=self);
            return
        text.delete(pos, newpos)
        text.insert(pos, newtext)
        end_pos = "%s+%dc" % (pos, len(newtext))
        if mark: self.mark_text(pos, end_pos)
        return pos, end_pos

    def replace_all(self):
        self.text.mark_set("insert", "1.0")  # 将光标移到开头
        flag = False  # 标志是否已有文字被替换

        # 以下代码会导致无限替换, 使程序卡死, 新的代码修复了该bug
        # while self.replace(bell=False)!=-1:
        #    flag=True
        last = (0, 0)
        while True:
            result = self.replace(bell=False, mark=False)
            if result is None: break
            flag = True
            result = self.findnext('start', bell=False, mark=False)
            if result is None: return
            ln, col = result[0].split('.')
            ln = int(ln);
            col = int(col)
            # 判断新的偏移量是增加还是减小
            if ln < last[0] or (ln == last[0] and col < last[1]):
                self.mark_text(*result)  # 已完成一轮替换
                break
            last = ln, col
        if not flag: bell_()
#代码替换================================================
def fz(nr):
    pyperclip.copy(nr)
def bzj(mc, xs, dm2):
    # 标准节
    #Label(mc, text=xs).pack()
    def dm():
        fz(dm2)
    t.Button(mc, text=xs, command=dm,bootstyle=sjanys()).pack()
    # 已上为标准节
def dmts():  # 代码提示
    win = Toplevel()
    canvas = Canvas(win, width=200, height=310000, scrollregion=(0, 0, 820, 2050))  # 创建canvas
    dmts = Frame(canvas, height=100)  # 用框架换掉窗口，方便滚动
    win.title("代码提示")
    win.geometry("300x300")
    # sb = Scrollbar(dmts)
    # sb.pack(side=RIGHT, fill=Y)
    # 这个scrollbar没有用了，看下面那个

    # 标准节
    # Label(dmts, text="print()，输出").pack()
    # def dm():
    #     fz("print()")
    # Button(dmts, text="复制代码", command=dm).pack()
    # 已上为标准节
    for i in range(30):
        Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()

    Label(dmts, text="代码提示", font=20).pack()
    Label(dmts, text="点击按钮复制代码").pack()
    bzj(dmts,"print()，输出","print()")
    bzj(dmts,"'',字符串","''")
    bzj(dmts, "'''''',字符串", "''''''")
    bzj(dmts, "input(),输入", "input()")
    bzj(dmts, "def():,定义函数", "def():")
    bzj(dmts, "if,判断语句", "if")
    bzj(dmts, "import,导库语句", "import")
    bzj(dmts, "from import*,导库", "from import*")
    bzj(dmts,"import math,导入math库","import math")
    bzj(dmts,"math.pi, 圆周率，","math.pi")
    bzj(dmts,"math.ceil(x), 对x向上取整","math.ceil(x)")
    bzj(dmts,"math.floor(x), 对x向下取整","math.floor(x)")
    bzj(dmts,"math.pow(x), 对x向上取整","math.pow(x)")
    bzj(dmts,"math.sqrt(x), x的平方根","math.sqrt(x)")
    bzj(dmts,"from tkinter import*,导入tkinter库","from tkinter import*")
    bzj(dmts,"= Tk(),创建窗口","= Tk()")
    bzj(dmts,".geometry(),窗口大小", ".geometry()")
    bzj(dmts, ".title(),窗口标题", ".title()")
    bzj(dmts, ".update(),窗口刷新", ".update()")
    bzj(dmts, ".iconbitmap(),窗口图标", ".iconbitmap()")
    bzj(dmts, "= PhotoImage(file=),加载图片", "= PhotoImage(file=)")
    bzj(dmts,"Label(),标签","Label()")
    bzj(dmts,"Button(),按钮","Button()")
    bzj(dmts,"Entry(),输入框","Entry()")
    bzj(dmts,"Text(),多行输入","Text()")
    bzj(dmts,".pack(),展示",".pack()")
    bzj(dmts,"width=,宽","width=")
    bzj(dmts,"height=,高","height=")
    bzj(dmts, "image=,图片", "image=")
    bzj(dmts, "bg=,文字颜色", "bg=")
    bzj(dmts, "fg=,背景颜色", "fg=")
    bzj(dmts, "text=,文字", "text=")
    bzj(dmts,".mainloop(),循环刷新",".mainloop()")
    bzj(dmts,"import os,导入os","import os")
    bzj(dmts,"os.system(),输入指令","os.system()")
    bzj(dmts,"= os.popen().read(),获取终端内容","= os.popen().read()")

    vbar = t.Scrollbar(win, orient=VERTICAL, command=canvas.yview,bootstyle=sjgdtys())  # 竖直滚动条
    #vbar.place(x=280, y=0, height=300)
    vbar.pack(side=RIGHT,fill=Y)
    canvas.config(yscrollcommand=vbar.set)
    dmts.pack()  # 显示控件
    canvas.pack()
    canvas.create_window((90, 240), window=dmts)  # create_window,让他们互相绑定
    win.mainloop()
def dkwy(wz):#打卡网址，wz=网址
    import webbrowser as w
    w.open(wz)
def bfyy(yy):
    import os
    #file = r"D:\User\Dashujv\语音分析\data\声声慢.wav"
    os.system(yy)
def yy():
    yy = Toplevel()
    yy.title("背景音乐")
    yy.geometry("250x250")
    Label(yy,text="请输入音乐名称").pack()
    yymc = t.Combobox(yy, bootstyle=sjys())
    a = []
    path = os.getcwd()
    for i in os.listdir(path):
        a.append(i)
    if a == []:
        ts = Toplevel()
        ts.title("提示")
        Label(ts,text="当期目录下没有音乐！",font=("kaiti",50)).pack()
        ts.mainloop()
    yymc['values'] = a  # 设置下拉列表的值
    yymc.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标值
    yymc.pack()
    def bfyy2():
        bfyy(yymc.get())
    t.Button(yy,text="播放此音乐",command=bfyy2,bootstyle=sjanys()).pack()
    def drown():
        dkwy("https://y.qq.com/n/ryqq/songDetail/261435364")
    def STAY():
        dkwy("https://y.qq.com/n/ryqq/songDetail/0043EX2e2F6JCA")
    t.Button(yy,text="推荐音乐：drown",command=drown,bootstyle=sjanys()).pack()
    t.Button(yy,text="推荐音乐：STAY", command=STAY,bootstyle=sjanys()).pack()
    yy.mainloop()
def kgl():
    #检测镜像源
    try:
        with open("设置\\jxy.txt", "r", encoding="UTF-8") as file:
            jxy = file.read()
    except:
        jxy = ""

    def jxysz():
        win = t.Window()
        win.title("更改镜像源")
        win.geometry("250x250")
        Label(win, text="更改镜像源", font=50).pack()
        def qhjxy():
            def cq():
                import sys
                import os
                """Restarts the current program.
                Note: this function does not return. Any cleanup action (like
                saving data) must be done before calling this function."""
                python = sys.executable
                os.execl(python, python, *sys.argv)
            def bc():
                nr = "-i" + "https://pypi.tuna.tsinghua.edu.cn/simple/"
                lj = os.getcwd()
                try:
                    os.mkdir(lj + "\\设置")
                    with open("设置\\jxy.txt", "w", encoding="UTF-8") as file:
                        file.write(nr)
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    Button(ts, text="重启程序", command=cq).pack()
                    ts.mainloop()
                except:
                    with open("设置\\fg.txt", "w", encoding="UTF-8") as file:
                        file.write(nr)
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    Button(ts, text="重启程序", command=cq).pack()
                    ts.mainloop()
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                Button(ts, text="重启程序", command=cq).pack()
                ts.mainloop()
            bc()
        Checkbutton(win,text="清华镜像源",command=qhjxy).pack()
        win.mainloop()
    # 函数区
    def zxzl(zl):
        zdnr = os.popen(zl).read()
        import tkinter as t
        zd = t.Toplevel()
        zd.title("终端")
        # Label(zd,text=zdnr,fg=ztys).pack()
        t = Text(zd, fg=ztys)
        t.insert(1.0, zdnr)
        t.pack(fill=BOTH, expand=1)
        zd.mainloop()

    def gxpip():
        os.system("python -m pip install --upgrade pip")

    def yazk():
        zxzl("pip list")

    def xzk():
        xzk = Toplevel()
        xzk.geometry("250x250")
        xzk.title("卸载库")
        Label(xzk, text="请输入库名").pack()
        km = Entry(xzk)
        km.pack()

        def ksxzk():
            dm = "pip uninstall " + km.get()
            os.system(dm)

        Button(xzk, text="卸载该库", command=ksxzk).pack()
        xzk.mainloop()

    def gxkdy():
        gxkdy = Toplevel()
        gxkdy.geometry("250x250")
        gxkdy.title("更新库")
        Label(gxkdy, text="请输入库名", font=20).pack()
        km = Entry(gxkdy)
        km.pack()

        def gxgbk():
            dm = "pip install --upgrade " + km.get()
            os.system(dm)

        Button(gxkdy, text="更新该库", command=gxgbk).pack()

    def azkdy():
        azkdy = Toplevel()
        azkdy.geometry("250x100")
        azkdy.title("安装库导引")

        def abbazk():
            abbazk = Toplevel()
            abbazk.geometry("300x300")
            abbazk.title("按版本安装库")
            Label(abbazk, text="请输入库名", font=15).pack()
            km = Entry(abbazk)
            km.pack()
            Label(abbazk, text="请输入要安装的版本号", font=15).pack()
            bb = Entry(abbazk)
            bb.pack()

            def bbnr():
                bbdm = "pip install " + km.get() + "==" + bb.get() + jxy
                os.system(bbdm)

            def pyplwy():
                def dkwy(wz):  # 打卡网址，wz=网址
                    import webbrowser as w
                    w.open(wz)

                wywz = "https://pypi.org/project/" + km.get() + "/"
                dkwy(wywz)

            Button(abbazk, text="安装该库", command=bbnr).pack()
            Button(abbazk, text="查看该库的PyPl网页", command=pyplwy).pack()
            abbazk.mainloop()

        def azk():
            azk = Toplevel()
            azk.geometry("300x300")
            azk.title("安装库")
            Label(azk, text="请输入库名", font=15).pack()
            e = Entry(azk)
            e.pack()

            def nr():
                dm = "pip install " + e.get() + jxy
                os.system(dm)

            Button(azk, text="安装该库", command=nr).pack()

            def pyplwy():
                def dkwy(wz):  # 打卡网址，wz=网址
                    import webbrowser as w
                    w.open(wz)

                wywz = "https://pypi.org/project/" + e.get() + "/"
                dkwy(wywz)

            Button(azk, text="查看该库的PyPl网页", command=pyplwy).pack()
            azk.mainloop()

        Button(azkdy, text="安装库", command=azk).pack()
        Button(azkdy, text="按版本安装库", command=abbazk).pack()
        azkdy.mainloop()

    # 主窗口
    window = Toplevel()
    window.geometry("280x260")
    window.title("奥利给库管理程序")
    Label(window, text="奥利给库管理程序", font=("kaiti", 20)).pack()
    Label(window, text="制作团队：奥利给硬件科技工作室", font="kaiti").pack()
    t.Button(window, text="更新pip库", command=gxpip,bootstyle=sjanys()).pack()
    t.Button(window, text="查看已安装库", command=yazk,bootstyle=sjanys()).pack()
    t.Button(window, text="安装新库", command=azkdy,bootstyle=sjanys()).pack()
    t.Button(window, text="更新库", command=gxkdy,bootstyle=sjanys()).pack()
    t.Button(window, text="卸载库", command=xzk,bootstyle=sjanys()).pack()
    t.Button(window, text="设置安装镜像源", command=jxysz,bootstyle=sjanys()).pack()
    window.mainloop()
def dqwjms(pat):
    if ".py" in pat:
        def xjbc():
            from tkinter import scrolledtext
            from threading import Thread, RLock

            class Main(Toplevel):
                def __init__(self):
                    super().__init__()
                    self.thread_lock = RLock()
                    self.txt = ""
                    self._main()

                def _main(self):
                    self.resizable(True, True)
                    self.geometry("800x600")
                    self.mc2 = pat
                    self.title(self.mc2)
                    self.edit_frame = Canvas(self, height=600, width=800,
                                             bg="white", highlightthickness=0)
                    self.edit_frame.pack()
                    self.line_text = Text(self.edit_frame, width=7, height=600, spacing3=5,
                                          bg="#DCDCDC", bd=0, font=(zt, 14), takefocus=0, state="disabled",
                                          cursor="arrow")
                    self.line_text.pack(side="left", expand=True)
                    self.update()
                    self.text = scrolledtext.ScrolledText(self.edit_frame, height=1, wrap="none", spacing3=5,
                                                          width=self.winfo_width() - self.line_text.winfo_width(),
                                                          bg="white",
                                                          bd=0, font=(zt, 14), undo=True, insertwidth=1)

                    # 代码补全=====================
                    def bqzt(event):
                        import random
                        import os
                        hcpath = os.getcwd() + "\\缓存文件（删除了不会造成影响）"
                        # hcpath = repr(hcpath_no)
                        while True:
                            try:
                                import os
                                name = os.listdir(hcpath)
                                self.mc3 = str(random.randint(1, 10000000000000000000000000000000000000000))
                                if self.mc3 not in name:
                                    break
                            except:
                                self.mc3 = str(random.randint(1, 10000000000000000000000000000000000000000))
                                break

                        lj = os.getcwd()
                        try:
                            os.mkdir(lj + "\\缓存文件（删除了不会造成影响）")
                            self.mc3 = "缓存文件（删除了不会造成影响）//" + self.mc3
                        except:
                            self.mc3 = "缓存文件（删除了不会造成影响）//" + self.mc3

                        def bc():
                            a = self.text.get("1.0", "end")
                            with open(self.mc3, "w+", encoding="UTF-8") as file:
                                file.write(a)

                        bc()
                        # 创建函数列表
                        dmlist = []
                        # 遍历文件获取代码库
                        # 读取配置
                        try:
                            with open("设置\\python.txt", "r", encoding="UTF-8") as file:
                                for line in file:
                                    sb = len(line)
                                    sb = sb + 1
                                    sb2 = sb - 2
                                    wbd = line[sb2:sb]
                                    if wbd == "\n":
                                        line = line[0:sb2]
                                    dmlist.append(line)
                        except:
                            dmlist = ["print", 'def']
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
                        import linecache
                        text = linecache.getline(self.mc3, linenum2)
                        ftext = text[0:lie2]
                        print(ftext)  # 第一个输出内容，为切分后有可能是半代码的内容
                        # 利用分词，获取用户输入的那半个函数
                        import jieba
                        feilist = jieba.lcut(ftext)
                        print(feilist)  # 第二个输出，为切分后的列表

                        # 智能补全系统
                        for i in range(1, linenum2):
                            import linecache
                            fxbl = linecache.getline(self.mc3, i)
                            if " = " in fxbl:
                                import jieba
                                yslist = jieba.lcut(fxbl)
                                dyfcdw = yslist.index("=")
                                dyfcdw = dyfcdw - 2
                                blm = yslist[dyfcdw]
                                dmlist.append(blm)

                        for i in range(1, linenum2):
                            import linecache
                            fxbl = linecache.getline(self.mc3, i)
                            if "def " in fxbl:
                                import jieba
                                yslist = jieba.lcut(fxbl)
                                dyfcdw = yslist.index("def")
                                dyfcdw = dyfcdw + 2
                                blm = yslist[dyfcdw]
                                blm = blm + "()"
                                dmlist.append(blm)

                        def power(n):
                            jian = n + n
                            far = n - jian
                            return far

                        a = 1
                        while True:
                            try:
                                if feilist[power(a)] == "\n":
                                    a = a + 1
                                else:
                                    print(feilist[power(a)])  # 第三个输出，为去除换行符后的内容
                                    bandm = feilist[power(a)]
                                    break
                            except:
                                bandm = "   "
                                break
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
                        print(hx)  # 最后一个输出，推荐列表

                        # 插入组件
                        def cr(bandm, xzdm):  # bandm用户输入的那一半代码，xzdm用户选择的代码
                            bancd = len(bandm)
                            xzcd = len(xzdm)
                            bqdm = xzdm[bancd:xzcd]
                            fz(bqdm)

                            def zt(event=None):
                                global root
                                self.text.event_generate('<<Paste>>')

                            zt()

                        # 补全弹窗
                        win = Toplevel()
                        win.overrideredirect(True)
                        win.wm_attributes('-topmost', 1)

                        def fuck():
                            win.destroy()

                        def fuck2(event):
                            win.destroy()

                        win.after(10000, fuck)
                        x = win.winfo_pointerx() - 1
                        y = win.winfo_pointery() - 1
                        x2 = str(x)
                        y2 = str(y)
                        hxs = len(hx)
                        if hxs > 6:
                            k = 132
                        else:
                            k = hxs * 21
                        k2 = str(k)
                        ckdx = "100x" + k2
                        weizhi = ckdx + "+" + x2 + "+" + y2
                        win.geometry(weizhi)
                        sc = t.Scrollbar(win, bootstyle=sjgdtys())
                        sc.pack(side=RIGHT, fill=Y)
                        hxlist = Listbox(win, yscrollcommand=sc.set)
                        hxlist.pack(expand=True)
                        hxlist.selection_set(first=0)
                        # 滚动条动，列表跟着动
                        sc.config(command=hxlist.yview)
                        if hx == ["无建议"]:
                            hxlist.insert(END, "无建议")
                            win.bind("<Alt_R>", fuck2)
                            win.bind("<Alt_L>", fuck2)
                        else:
                            for item in hx:
                                hxlist.insert(END, item)  # END表示每插入一个都是在最后一个位置

                            def crzb(event):
                                for i in hxlist.curselection():
                                    cr(bandm, hxlist.get(i))
                                    win.destroy()

                            win.bind("<Return>", crzb)
                            win.bind("<Double-Button-1>", crzb)
                            win.bind("<Alt_R>", fuck2)
                            win.bind("<Alt_L>", fuck2)
                        win.mainloop()

                    self.text.bind("<Alt_L>", bqzt)
                    self.text.bind("<Alt_R>", bqzt)
                    # 代码补全底======================

                    # 自动缩进
                    self.text.bind("<Return>", self.enter)
                    # ======

                    # 缩进规范
                    def tab(event):
                        self.text.insert('insert', '    ')
                        self.get_txt_thread()

                    self.text.bind("<Tab>", tab)
                    # ======

                    self.text.vbar.configure(command=self.scroll)
                    self.text.pack(side="left", fill="both")
                    self.line_text.bind("<MouseWheel>", self.wheel)
                    self.text.bind("<MouseWheel>", self.wheel)
                    self.text.bind("<Control-v>", lambda e: self.get_txt_thread())
                    self.text.bind("<Control-V>", lambda e: self.get_txt_thread())
                    self.text.bind("<Key>", lambda e: self.get_txt_thread())
                    self.show_line()
                    # 代码高亮（text后）
                    if ColorDelegator:
                        colorobj = None
                        # 设置代码高亮显示
                        _codefilter = ColorDelegator()

                        def defines():
                            dics = {"foreground": "", "background": "white"}
                            self = _codefilter
                            # window.text = text
                            # auto = autocomplete.AutoComplete(window)
                            self.tagdefs = {
                                "COMMENT": {"foreground": "green", "background": "white"},
                                "KEYWORD": {"foreground": "blue", "background": "white"},
                                "BUILTIN": {"foreground": "gray", "background": "white"},
                                "STRING": {"foreground": "green", "background": "white"},
                                "DEFINITION": {"foreground": "purple", "background": "white"},
                                "SYNC": {'background': "pink", 'foreground': "red"},
                                "TODO": {'background': "pink", 'foreground': "red"},
                                "ERROR": {"foreground": "red", "background": "white"},
                                # The following is used by ReplaceDialog:
                                "hit": {"foreground": None, "background": "white"},
                            }

                            # if DEBUG: print('tagdefs', self.tagdefs)

                        _codefilter.LoadTagDefs = defines
                        if not colorobj:
                            colorobj = Percolator(self.text)  # Text名称
                        colorobj.insertfilter(_codefilter)
                        # 代码高亮（text后）

                    if not autocomplete:
                        pass
                    else:
                        self.text = self.text
                        auto = autocomplete.AutoComplete(self)

                    def yxjb():
                        a = self.text.get("1.0", "end")
                        with open(self.mc2, "w", encoding="UTF-8") as file:
                            file.write(a)
                        # 读取配置
                        try:
                            with open("设置\\jsq.txt", "r", encoding="UTF-8") as file:
                                jsqaa = file.read()
                                jsqxz = jsqaa
                        except:
                            jsqxz = "F"
                        ###
                        if jsqxz == "F":
                            dm = "python -i " + self.mc2
                        else:
                            with open("设置\\jsqpath.txt", "r", encoding="UTF-8") as file:
                                pathjsq = file.read()
                            dm = pathjsq + " -i " + self.mc2
                        os.system(dm)

                    def yx():
                        from threading import Thread
                        t2 = Thread(target=yxjb)
                        t2.start()

                    def bc():
                        a = self.text.get("1.0", "end")
                        with open(self.mc2, "w", encoding="UTF-8") as file:
                            file.write(a)

                    # 自动保存
                    # 读取用户设置
                    try:
                        with open("设置\\zdbc.txt", "r", encoding="UTF-8") as file:
                            zd = file.read()
                            bcsz = zd
                    except:
                        bcsz = "F"
                    if bcsz == "T":
                        def zdbc(event):
                            a = self.text.get("1.0", "end")
                            with open(self.mc2, "w", encoding="UTF-8") as file:
                                file.write(a)

                        self.bind("<Key>", zdbc)
                    # 自动保存

                    def dq():
                        try:
                            with open(self.mc2, "r", encoding="UTF-8") as file:
                                wj = file.read()
                                return wj
                        except:
                            ts = Toplevel()
                            ts.title("提示")
                            Label(ts, text="文件不存在", font=("kaiti",50)).pack()
                            ts.mainloop()

                    # 插入文本
                    texts = dq()
                    self.text.insert(1.0, texts)
                    self.get_txt_thread()
                    # 按钮
                    # Button(self.edit_frame,text="运行程序",command=yx,fg=ztys).pack(side=RIGHT)
                    # Button(self.edit_frame, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
                    # Button(self.edit_frame, text="库管理", command=kgl,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="代码提示", command=dmts,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="更多插件", command=cj,fg=ztys).pack(side=LEFT)
                    # Button(self, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
                    def cmd():
                        os.startfile("cmd")

                    def cx():
                        self.text.edit_undo()

                    def hf():
                        self.text.edit_redo()

                    # 搜索系统===========================================================
                    def Init():
                        global text

                        x = self.text.get("1.0", END)
                        self.text.delete("1.0", END)
                        # 重新插入文本
                        self.text.insert(INSERT, x)

                    def fun():
                        '查找所有满足条件的字符串'
                        global x, li
                        start = "1.0"
                        while True:
                            pos = self.text.search(x, start, stopindex=END)
                            if not pos:  # 没有找到
                                # if len(li) != 0:
                                # print li
                                break
                            li.append(pos)
                            # len(x) 避免一个字符被查找多次
                            start = pos + "+%dc" % len(x)

                    # num 设置当前要显示的是第几个
                    self.num = 0
                    # 用于查看当前输入的字符串和之前的字符串是否相同，如果相同的话，则要从第一个开始查找，初始化num的值
                    self.str1 = ""
                    self.str2 = ""

                    def find1():
                        global x, li, num, text, str1, str2
                        li = []
                        Init()
                        x = self.e1.get()
                        if len(x) == 0:
                            showerror('错误', '请输入内容')
                            return

                        str1 = x
                        # 如果说当前的str1是新输入的，则num要从0开始查找
                        if self.str2 != self.str1:
                            self.num = 0
                        # 用现在的值把之前的值覆盖
                        self.str2 = self.str1
                        fun()
                        if len(li) == 0:
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        if self.num == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                            showinfo("查找结束", "找不到%s了" % x)
                            self.num = 0
                            return
                        # 获取当前颜色要变化的位置
                        i = li[self.num]
                        self.num += 1

                        Init()
                        k, t = i.split(".")
                        t = str(len(x) + int(t))
                        j = k + '.' + t
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                        self.text.see(i)
                        li = []

                    def find2():
                        global x, li, num, text, str1, str2
                        li = []
                        Init()
                        x = self.e2.get()
                        if len(x) == 0:
                            showerror('错误', '请输入内容')
                            return

                        self.str1 = x
                        # 如果说当前的str1是新输入的，则num要从-1开始查找
                        if self.str2 != self.str1:
                            num = -1
                        # 用现在的值把之前的值覆盖
                        self.str2 = self.str1
                        fun()
                        if len(li) == 0:
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        if abs(num + 1) == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                            showinfo("查找结束", "找不到%s了" % x)
                            self.num = -1
                            return
                        # 获取当前颜色要变化的位置
                        i = li[self.num]
                        self.num -= 1

                        Init()
                        k, t = i.split(".")
                        t = str(len(x) + int(t))
                        j = k + '.' + t
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                        self.text.see(i)
                        li = []

                    def find3():
                        global x, li
                        # 每次进行一次全部查找，一定要先把li列表初始化
                        li = []
                        Init()
                        x = self.e3.get()
                        if len(x) == 0:  # 如果说从输入框中得不到内容，则直接终止，不进行判断
                            showerror("错误", "请输入内容")
                            return
                        fun()
                        if len(li) == 0:  # 没有找到，直接终止即可
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        for i in li:
                            k, t = i.split(".")
                            # 加上字符串的长度，即判断能达到的位置
                            t = str(len(x) + int(t))
                            # 重新连接
                            j = k + '.' + t
                            # 加特殊的前景色和背景色
                            self.text.tag_add("tag1", i, j)
                            self.text.tag_config("tag1", background="yellow", foreground="blue")
                        li = []

                    def change():
                        global top, text
                        # 如果要关闭窗口，则获取Text组件中的所有文本，
                        # 再重新输入，防止查找的结果对Text文本框产生影响，然后关闭即可
                        Init()
                        # 刷新，关闭顶层窗口
                        top.withdraw()

                    # Entry框
                    e1 = 0
                    e2 = 0
                    e3 = 0

                    x = 0
                    li = []
                    top = 0

                    def create():
                        global e1, e2, e3, top
                        top = Toplevel()
                        top.title("查找")
                        # 设置顶层窗口的大小不可变
                        # top.maxsize(250, 110)
                        # top.minsize(250, 110)

                        # 两个按钮和两个Entry输入框
                        self.e1 = t.Entry(top, bootstyle=sjys())
                        self.e1.grid(row=0, column=0)
                        t.Button(top, text="查找下一个", width=10, command=find1, bootstyle=sjanys()).grid(row=0,
                                                                                                      column=1)
                        self.e2 = t.Entry(top, bootstyle=sjys())
                        self.e2.grid(row=1, column=0)
                        t.Button(top, text="查找上一个", width=10, command=find2, bootstyle=sjanys()).grid(row=1,
                                                                                                      column=1)
                        self.e3 = t.Entry(top, bootstyle=sjys())
                        self.e3.grid(row=2, column=0)
                        t.Button(top, text="查找全部", width=10, command=find3, bootstyle=sjanys()).grid(row=2,
                                                                                                     column=1)

                        # 当顶层窗口关闭的时候，所有的设置还原
                        top.protocol(name='WM_DELETE_WINDOW', func=change)
                    # ===================================================================================

                    # 替换===============================================================
                    def replace():
                        """替换"""
                        self.coding = StringVar(self)
                        replace_dlg = ReplaceDialog(self, self.text)
                        # replace_dlg.attributes("-topmost", True)
                        replace_dlg.show()
                    # ==================================================================

                    menu = Menu(self, tearoff=0)
                    menu.add_command(label="运行代码", command=yx)
                    menu.add_command(label="保存文件", command=bc)
                    menu.add_command(label="撤销", command=cx)
                    menu.add_command(label="恢复", command=hf)
                    menu.add_command(label="搜索", command=create)
                    menu.add_command(label="替换", command=replace)
                    menu.add_command(label="库管理", command=kgl)
                    menu.add_command(label="背景音乐", command=yy)
                    menu.add_command(label="代码提示", command=dmts)
                    menu.add_command(label="更多插件", command=cj)
                    menu.add_command(label="终端", command=cmd)

                    def popupmenu(event):
                        menu.post(event.x_root, event.y_root)

                    self.config(menu=menu)
                    self.bind("<Button-3>", popupmenu)

                # 自动缩进
                def enter(self, *args):
                    self.i = 0
                    a = self.text.index('insert')
                    a = float(a)
                    aa = int(a)
                    b = self.text.get(float(aa), a).replace('\n', '')
                    c = b
                    if b[-1:] == ':':
                        i = 0
                        while True:
                            if b[:4] == '    ':
                                b = b[4:]
                                i += 1
                            else:
                                break
                        self.i = i + 1
                    else:
                        i = 0
                        while True:
                            if b[:4] == '    ':
                                b = b[4:]
                                i += 1
                            else:
                                break
                        self.i = i
                        if c.strip() == 'break' or c.strip() == 'return' or c.strip() == 'pass' or c.strip() == 'continue':
                            self.i -= 1
                    self.text.insert('insert', '\n')
                    for j in range(self.i):
                        self.text.insert('insert', '    ')
                    self.get_txt_thread()
                    return 'break'

                def wheel(self, event):
                    self.line_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return "break"

                def scroll(self, *xy):
                    self.line_text.yview(*xy)
                    self.text.yview(*xy)

                def get_txt_thread(self):
                    Thread(target=self.get_txt).start()

                def get_txt(self):
                    self.thread_lock.acquire()
                    if self.txt != self.text.get("1.0", "end")[:-1]:
                        self.txt = self.text.get("1.0", "end")[:-1]
                        self.show_line()
                    else:
                        self.thread_lock.release()

                def show_line(self):
                    sb_pos = self.text.vbar.get()
                    self.line_text.configure(state="normal")
                    self.line_text.delete("1.0", "end")
                    txt_arr = self.txt.split("\n")
                    if len(txt_arr) == 1:
                        self.line_text.insert("1.1", " 1")
                    else:
                        for i in range(1, len(txt_arr) + 1):
                            self.line_text.insert("end", " " + str(i))
                            if i != len(txt_arr):
                                self.line_text.insert("end", "\n")
                    if len(sb_pos) == 4:
                        self.line_text.yview_moveto(0.0)
                    elif len(sb_pos) == 2:
                        self.line_text.yview_moveto(sb_pos[0])
                        self.text.yview_moveto(sb_pos[0])
                    self.line_text.configure(state="disabled")
                    try:
                        self.thread_lock.release()
                    except RuntimeError:
                        pass

            run = Main()
            run.mainloop()
            # # 主窗口
            # mc2 = e.get()
            # window = Tk()
            # window.title(mc2)
            # # 设置text
            # text = Text(window, font=zt, fg=fg, undo=True)
            # scroll = Scrollbar(window)
            # # 放到窗口的右侧, 填充Y竖直方向
            # scroll.pack(side=RIGHT, fill=Y)
            #
            # # 两个控件关联
            # scroll.config(command=text.yview)
            # text.config(yscrollcommand=scroll.set)
            #
            # text.pack(fill=BOTH, expand=1)
            #
            # if ColorDelegator:
            #     colorobj = None
            #     # 设置代码高亮显示
            #     _codefilter = ColorDelegator()
            #
            #     def defines():
            #         dics = {"foreground": "", "background": "white"}
            #         self = _codefilter
            #         self.tagdefs = {
            #             "COMMENT": {"foreground": "green", "background": "white"},
            #             "KEYWORD": {"foreground": "blue", "background": "white"},
            #             "BUILTIN": {"foreground": "gray", "background": "white"},
            #             "STRING": {"foreground": "green", "background": "white"},
            #             "DEFINITION": {"foreground": "purple", "background": "white"},
            #             "SYNC": {'background': "pink", 'foreground': "red"},
            #             "TODO": {'background': "pink", 'foreground': "red"},
            #             "ERROR": {"foreground": "red", "background": "white"},
            #             # The following is used by ReplaceDialog:
            #             "hit": {"foreground": None, "background": "white"},
            #         }
            #
            #         # if DEBUG: print('tagdefs', self.tagdefs)
            #
            #     _codefilter.LoadTagDefs = defines
            #     if not colorobj:
            #         colorobj = Percolator(text)
            #     colorobj.insertfilter(_codefilter)
            #
            # def yx():
            #     a = text.get("1.0", "end")
            #     with open(mc2, "w", encoding="UTF-8") as file:
            #         file.write(a)
            #     dm = "python -i " + mc2
            #     os.system(dm)
            #
            # def bc():
            #     a = text.get("1.0", "end")
            #     with open(mc2, "w", encoding="UTF-8") as file:
            #         file.write(a)
            #
            # def dq():
            #     try:
            #         with open(mc2, "r", encoding="UTF-8") as file:
            #             wj = file.read()
            #             return wj
            #     except:
            #         ts = Tk()
            #         ts.title("提示")
            #         Label(ts, text="文件不存在", font=("kaiti",50), fg=ztys).pack()
            #         ts.mainloop()
            #
            # # 插入文本
            # texts = dq()
            # text.insert(1.0, texts)
            # # 按钮
            # Button(window, text="运行程序", command=yx, fg=ztys).pack(side=RIGHT)
            # Button(window, text="保存代码", command=bc, fg=ztys).pack(side=RIGHT)
            # Button(window, text="库管理", command=kgl, fg=ztys).pack(side=LEFT)
            # Button(window, text="背景音乐", command=yy, fg=ztys).pack(side=LEFT)
            # Button(window, text="代码提示", command=dmts, fg=ztys).pack(side=LEFT)
            # Button(window, text="更多插件", command=cj, fg=ztys).pack(side=LEFT)
            #
            # def cmd():
            #     os.startfile("cmd")
            #
            # Button(window, text="终端", command=cmd, fg=ztys).pack(side=LEFT)
            #
            # def cx():
            #     text.edit_undo()
            #
            # def hf():
            #     text.edit_redo()
            #
            # menu = Menu(window, tearoff=0)
            # menu.add_command(label="撤销", command=cx)
            # menu.add_separator()
            # menu.add_command(label="恢复", command=hf)
            # menu.add_separator()
            #
            # def popupmenu(event):
            #     menu.post(event.x_root, event.y_root)
            #
            # window.bind("<Button-3>", popupmenu)
            # window.mainloop()

        xjbc()
    elif ".html" in pat:
        def xjbc():
            from tkinter import scrolledtext
            from threading import Thread, RLock

            class Main(Toplevel):
                def __init__(self):
                    super().__init__()
                    self.thread_lock = RLock()
                    self.txt = ""
                    self._main()

                def _main(self):
                    self.resizable(True, True)
                    self.geometry("800x600")
                    self.mc2 = pat
                    self.title(self.mc2)
                    from tkinter import Canvas
                    self.edit_frame = Canvas(self, height=600, width=800,
                                             bg="white", highlightthickness=0)
                    self.edit_frame.pack()
                    from tkinter import Text
                    self.line_text = Text(self.edit_frame, width=7, height=600, spacing3=5,
                                          bg="#DCDCDC", bd=0, font=(zt, 14), takefocus=0, state="disabled",
                                          cursor="arrow")
                    self.line_text.pack(side="left", expand=True)
                    self.update()
                    self.text = scrolledtext.ScrolledText(self.edit_frame, height=1, wrap="none", spacing3=5,
                                                          width=self.winfo_width() - self.line_text.winfo_width(),
                                                          bg="white",
                                                          bd=0, font=(zt, 14), undo=True, insertwidth=1)

                    # 代码补全头
                    from idlelib.autocomplete import AutoComplete
                    def dmbq():
                        AutoComplete(editwin=self)

                    # 代码补全底

                    # 缩进规范
                    def tab(event):
                        self.text.insert('insert', '    ')
                        self.get_txt_thread()

                    self.text.bind("<Tab>", tab)
                    # ======

                    self.text.vbar.configure(command=self.scroll)
                    self.text.pack(side="left", fill="both")
                    self.line_text.bind("<MouseWheel>", self.wheel)
                    self.text.bind("<MouseWheel>", self.wheel)
                    self.text.bind("<Control-v>", lambda e: self.get_txt_thread())
                    self.text.bind("<Control-V>", lambda e: self.get_txt_thread())
                    self.text.bind("<Key>", lambda e: self.get_txt_thread())
                    self.show_line()
                    # 代码高亮（text后）
                    if ColorDelegator:
                        colorobj = None
                        # 设置代码高亮显示
                        _codefilter = ColorDelegator()

                        def defines():
                            dics = {"foreground": "", "background": "white"}
                            self = _codefilter
                            # window.text = text
                            # auto = autocomplete.AutoComplete(window)
                            self.tagdefs = {
                                "COMMENT": {"foreground": "green", "background": "white"},
                                "KEYWORD": {"foreground": "blue", "background": "white"},
                                "BUILTIN": {"foreground": "gray", "background": "white"},
                                "STRING": {"foreground": "green", "background": "white"},
                                "DEFINITION": {"foreground": "purple", "background": "white"},
                                "SYNC": {'background': "pink", 'foreground': "red"},
                                "TODO": {'background': "pink", 'foreground': "red"},
                                "ERROR": {"foreground": "red", "background": "white"},
                                # The following is used by ReplaceDialog:
                                "hit": {"foreground": None, "background": "white"},
                            }

                            # if DEBUG: print('tagdefs', self.tagdefs)

                        _codefilter.LoadTagDefs = defines
                        if not colorobj:
                            colorobj = Percolator(self.text)  # Text名称
                        colorobj.insertfilter(_codefilter)
                        # 代码高亮（text后）

                    if not autocomplete:
                        pass
                    else:
                        self.text = self.text
                        auto = autocomplete.AutoComplete(self)

                    def yxjb():
                        a = self.text.get("1.0", "end")
                        with open(self.mc2, "w", encoding="UTF-8") as file:
                            file.write(a)
                        dm = self.mc2
                        os.system(dm)

                    def yx():
                        from threading import Thread
                        t2 = Thread(target=yxjb)
                        t2.start()

                    def bc():
                        a = self.text.get("1.0", "end")
                        with open(self.mc2, "w", encoding="UTF-8") as file:
                            file.write(a)

                    # 自动保存
                    # 读取用户设置
                    try:
                        with open("设置\\zdbc.txt", "r", encoding="UTF-8") as file:
                            zd = file.read()
                            bcsz = zd
                    except:
                        bcsz = "F"
                    if bcsz == "T":
                        def zdbc(event):
                            a = self.text.get("1.0", "end")
                            with open(self.mc2, "w", encoding="UTF-8") as file:
                                file.write(a)

                        self.bind("<Key>", zdbc)
                    # 自动保存

                    def dq():
                        try:
                            with open(self.mc2, "r", encoding="UTF-8") as file:
                                wj = file.read()
                                return wj
                        except:
                            ts = Toplevel()
                            ts.title("提示")
                            Label(ts, text="文件不存在", font=("kaiti",50)).pack()
                            ts.mainloop()

                    # 插入文本
                    texts = dq()
                    self.text.insert(1.0,texts)
                    self.get_txt_thread()

                    # 按钮
                    # Button(self.edit_frame,text="运行程序",command=yx,fg=ztys).pack(side=RIGHT)
                    # Button(self.edit_frame, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
                    # Button(self.edit_frame, text="库管理", command=kgl,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="代码提示", command=dmts,fg=ztys).pack(side=LEFT)
                    # Button(self.edit_frame, text="更多插件", command=cj,fg=ztys).pack(side=LEFT)
                    # Button(self, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
                    def cmd():
                        os.startfile("cmd")

                    def cx():
                        self.text.edit_undo()

                    def hf():
                        self.text.edit_redo()

                    # 搜索系统===========================================================
                    def Init():
                        global text

                        x = self.text.get("1.0", END)
                        self.text.delete("1.0", END)
                        # 重新插入文本
                        self.text.insert(INSERT, x)

                    def fun():
                        '查找所有满足条件的字符串'
                        global x, li
                        start = "1.0"
                        while True:
                            pos = self.text.search(x, start, stopindex=END)
                            if not pos:  # 没有找到
                                # if len(li) != 0:
                                # print li
                                break
                            li.append(pos)
                            # len(x) 避免一个字符被查找多次
                            start = pos + "+%dc" % len(x)

                    # num 设置当前要显示的是第几个
                    self.num = 0
                    # 用于查看当前输入的字符串和之前的字符串是否相同，如果相同的话，则要从第一个开始查找，初始化num的值
                    self.str1 = ""
                    self.str2 = ""

                    def find1():
                        global x, li, num, text, str1, str2
                        li = []
                        Init()
                        x = self.e1.get()
                        if len(x) == 0:
                            showerror('错误', '请输入内容')
                            return

                        str1 = x
                        # 如果说当前的str1是新输入的，则num要从0开始查找
                        if self.str2 != self.str1:
                            self.num = 0
                        # 用现在的值把之前的值覆盖
                        self.str2 = self.str1
                        fun()
                        if len(li) == 0:
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        if self.num == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                            showinfo("查找结束", "找不到%s了" % x)
                            self.num = 0
                            return
                        # 获取当前颜色要变化的位置
                        i = li[self.num]
                        self.num += 1

                        Init()
                        k, t = i.split(".")
                        t = str(len(x) + int(t))
                        j = k + '.' + t
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                        self.text.see(i)
                        li = []

                    def find2():
                        global x, li, num, text, str1, str2
                        li = []
                        Init()
                        x = self.e2.get()
                        if len(x) == 0:
                            showerror('错误', '请输入内容')
                            return

                        self.str1 = x
                        # 如果说当前的str1是新输入的，则num要从-1开始查找
                        if self.str2 != self.str1:
                            num = -1
                        # 用现在的值把之前的值覆盖
                        self.str2 = self.str1
                        fun()
                        if len(li) == 0:
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        if abs(num + 1) == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                            showinfo("查找结束", "找不到%s了" % x)
                            self.num = -1
                            return
                        # 获取当前颜色要变化的位置
                        i = li[self.num]
                        self.num -= 1

                        Init()
                        k, t = i.split(".")
                        t = str(len(x) + int(t))
                        j = k + '.' + t
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                        self.text.see(i)
                        li = []

                    def find3():
                        global x, li
                        # 每次进行一次全部查找，一定要先把li列表初始化
                        li = []
                        Init()
                        x = self.e3.get()
                        if len(x) == 0:  # 如果说从输入框中得不到内容，则直接终止，不进行判断
                            showerror("错误", "请输入内容")
                            return
                        fun()
                        if len(li) == 0:  # 没有找到，直接终止即可
                            showinfo("查找结果", "没有要查询的结果")
                            return
                        for i in li:
                            k, t = i.split(".")
                            # 加上字符串的长度，即判断能达到的位置
                            t = str(len(x) + int(t))
                            # 重新连接
                            j = k + '.' + t
                            # 加特殊的前景色和背景色
                            self.text.tag_add("tag1", i, j)
                            self.text.tag_config("tag1", background="yellow", foreground="blue")
                        li = []

                    def change():
                        global top, text
                        # 如果要关闭窗口，则获取Text组件中的所有文本，
                        # 再重新输入，防止查找的结果对Text文本框产生影响，然后关闭即可
                        Init()
                        # 刷新，关闭顶层窗口
                        top.withdraw()

                    # Entry框
                    e1 = 0
                    e2 = 0
                    e3 = 0

                    x = 0
                    li = []
                    top = 0

                    def create():
                        global e1, e2, e3, top
                        top = Toplevel()
                        top.title("查找")
                        # 设置顶层窗口的大小不可变
                        # top.maxsize(250, 110)
                        # top.minsize(250, 110)

                        # 两个按钮和两个Entry输入框
                        self.e1 = t.Entry(top, bootstyle=sjys())
                        self.e1.grid(row=0, column=0)
                        t.Button(top, text="查找下一个", width=10, command=find1, bootstyle=sjanys()).grid(row=0,
                                                                                                      column=1)
                        self.e2 = t.Entry(top, bootstyle=sjys())
                        self.e2.grid(row=1, column=0)
                        t.Button(top, text="查找上一个", width=10, command=find2, bootstyle=sjanys()).grid(row=1,
                                                                                                      column=1)
                        self.e3 = t.Entry(top, bootstyle=sjys())
                        self.e3.grid(row=2, column=0)
                        t.Button(top, text="查找全部", width=10, command=find3, bootstyle=sjanys()).grid(row=2,
                                                                                                     column=1)

                        # 当顶层窗口关闭的时候，所有的设置还原
                        top.protocol(name='WM_DELETE_WINDOW', func=change)
                    # ===================================================================================

                    # 替换===============================================================
                    def replace():
                        """替换"""
                        self.coding = StringVar(self)
                        replace_dlg = ReplaceDialog(self, self.text)
                        # replace_dlg.attributes("-topmost", True)
                        replace_dlg.show()
                    # ==================================================================

                    menu = Menu(self, tearoff=0)
                    menu.add_command(label="运行代码", command=yx)
                    menu.add_command(label="保存文件", command=bc)
                    menu.add_command(label="撤销", command=cx)
                    menu.add_command(label="恢复", command=hf)
                    menu.add_command(label="搜索", command=create)
                    menu.add_command(label="替换", command=replace)
                    menu.add_command(label="背景音乐", command=yy)
                    menu.add_command(label="代码提示", command=dmtshtml)
                    menu.add_command(label="更多插件", command=cj)
                    menu.add_command(label="终端", command=cmd)

                    def popupmenu(event):
                        menu.post(event.x_root, event.y_root)

                    self.config(menu=menu)
                    self.bind("<Button-3>", popupmenu)

                def wheel(self, event):
                    self.line_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return "break"

                def scroll(self, *xy):
                    self.line_text.yview(*xy)
                    self.text.yview(*xy)

                def get_txt_thread(self):
                    Thread(target=self.get_txt).start()

                def get_txt(self):
                    self.thread_lock.acquire()
                    if self.txt != self.text.get("1.0", "end")[:-1]:
                        self.txt = self.text.get("1.0", "end")[:-1]
                        self.show_line()
                    else:
                        self.thread_lock.release()

                def show_line(self):
                    sb_pos = self.text.vbar.get()
                    self.line_text.configure(state="normal")
                    self.line_text.delete("1.0", "end")
                    txt_arr = self.txt.split("\n")
                    if len(txt_arr) == 1:
                        self.line_text.insert("1.1", " 1")
                    else:
                        for i in range(1, len(txt_arr) + 1):
                            self.line_text.insert("end", " " + str(i))
                            if i != len(txt_arr):
                                self.line_text.insert("end", "\n")
                    if len(sb_pos) == 4:
                        self.line_text.yview_moveto(0.0)
                    elif len(sb_pos) == 2:
                        self.line_text.yview_moveto(sb_pos[0])
                        self.text.yview_moveto(sb_pos[0])
                    self.line_text.configure(state="disabled")
                    try:
                        self.thread_lock.release()
                    except RuntimeError:
                        pass

            run = Main()
            run.mainloop()
        xjbc()
    #         # 主窗口
    #         mc2 = e.get()
    #         window = Tk()
    #         window.title(mc2)
    #         # 设置text
    #         text = Text(window, font=zt, fg=fg, undo=True)
    #         scroll = Scrollbar(window)
    #         # 放到窗口的右侧, 填充Y竖直方向
    #         scroll.pack(side=RIGHT, fill=Y)
    #
    #         # 两个控件关联
    #         scroll.config(command=text.yview)
    #         text.config(yscrollcommand=scroll.set)
    #
    #         text.pack(fill=BOTH, expand=1)
    #
    #         def yx():
    #             a = text.get("1.0", "end")
    #             with open(mc2, "w", encoding="UTF-8") as file:
    #                 file.write(a)
    #             dm = mc2
    #             os.system(dm)
    #
    #         def bc():
    #             a = text.get("1.0", "end")
    #             with open(mc2, "w", encoding="UTF-8") as file:
    #                 file.write(a)
    #
    #         def dq():
    #             try:
    #                 with open(mc2, "r", encoding="UTF-8") as file:
    #                     wj = file.read()
    #                     return wj
    #             except:
    #                 ts = Tk()
    #                 ts.title("提示")
    #                 Label(ts, text="文件不存在", font=("kaiti",50), fg=ztys).pack()
    #                 ts.mainloop()
    #
    #         # 插入文本
    #         texts = dq()
    #         text.insert(1.0, texts)
    #
    #         # 代码高亮（text后）
    #         if ColorDelegator:
    #             colorobj = None
    #             # 设置代码高亮显示
    #             _codefilter = ColorDelegator()
    #
    #             def defines():
    #                 dics = {"foreground": "", "background": "white"}
    #                 self = _codefilter
    #                 self.tagdefs = {
    #                     "COMMENT": {"foreground": "green", "background": "white"},
    #                     "KEYWORD": {"foreground": "blue", "background": "white"},
    #                     "BUILTIN": {"foreground": "gray", "background": "white"},
    #                     "STRING": {"foreground": "green", "background": "white"},
    #                     "DEFINITION": {"foreground": "purple", "background": "white"},
    #                     "SYNC": {'background': "pink", 'foreground': "red"},
    #                     "TODO": {'background': "pink", 'foreground': "red"},
    #                     "ERROR": {"foreground": "red", "background": "white"},
    #                     # The following is used by ReplaceDialog:
    #                     "hit": {"foreground": None, "background": "white"},
    #                 }
    #
    #                 # if DEBUG: print('tagdefs', self.tagdefs)
    #
    #             _codefilter.LoadTagDefs = defines
    #             if not colorobj:
    #                 colorobj = Percolator(text)  # Text名称
    #             colorobj.insertfilter(_codefilter)
    #             # 代码高亮（text后）
    #
    #         # 按钮
    #         Button(window, text="运行代码", command=yx, fg=ztys).pack(side=RIGHT)
    #         Button(window, text="保存代码", command=bc, fg=ztys).pack(side=RIGHT)
    #         Button(window, text="背景音乐", command=yy, fg=ztys).pack(side=LEFT)
    #         Button(window, text="代码提示", command=dmtshtml, fg=ztys).pack(side=LEFT)
    #         Button(window, text="更多插件", command=cj, fg=ztys).pack(side=LEFT)
    #
    #         def cmd():
    #             os.startfile("cmd")
    #
    #         Button(window, text="终端", command=cmd, fg=ztys).pack(side=LEFT)
    #
    #         def cx():
    #             text.edit_undo()
    #
    #         def hf():
    #             text.edit_redo()
    #
    #         menu = Menu(window, tearoff=0)
    #         menu.add_command(label="撤销", command=cx)
    #         menu.add_separator()
    #         menu.add_command(label="恢复", command=hf)
    #         menu.add_separator()
    #
    #         def popupmenu(event):
    #             menu.post(event.x_root, event.y_root)
    #
    #         window.bind("<Button-3>", popupmenu)
    #         window.mainloop()
    #     xjbc()
    # else:
    #     ts = Tk()
    #     ts.title("提示")
    #     Label(ts,text="不支持当前文件格式，请输入正确的文件名，要加上后缀",font=("kaiti",20), fg=ztys).pack()
    #     ts.mainloop()
    else:
        win = Toplevel()
        win.title("提示-警告")
        Label(win,text="暂不支持当前格式！",font=("kaiti",70)).pack()
        win.mainloop()

def dqwj():
    xj = Toplevel()
    xj.title("读取文件")
    xj.geometry("250x250")
    Label(xj,text="请输入文件名称",font=20).pack()
    Label(xj, text="要加上后缀", font=20).pack()
    def xzpath():
        from tkinter import filedialog
        img_path = filedialog.askopenfilename()
        dqwjms(img_path)
    # e = Entry(xj)
    # e.pack()
    e = t.Combobox(xj,bootstyle=sjys())
    a = []
    path = os.getcwd()
    for i in os.listdir(path):
        if ".py" in i or ".html" in i:
            a.append(i)
    if a == []:
        xzpath()
    else:
        e['values'] = a     # 设置下拉列表的值
        e.current(0)    # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标值
        e.pack()
        def aaa():
            path = e.get()
            dqwjms(path)
        t.Button(xj, text="读取文件", command=aaa,bootstyle=sjanys()).pack()
        t.Button(xj, text="选取路径", command=xzpath, bootstyle=sjanys()).pack()
        xj.mainloop()

def xjwjpy():
    zck = Toplevel()
    zck.title("新建文件")
    zck.geometry("250x250")
    Label(zck,text="请输入文件名称",font=20).pack()
    Label(zck, text="不用加后缀", font=20).pack()
    mc = t.Entry(zck,bootstyle=sjys())
    mc.pack()
    def xjbc():
        from tkinter import scrolledtext
        from threading import Thread, RLock

        class Main(Toplevel):
            def __init__(self):
                super().__init__()
                self.thread_lock = RLock()
                self.txt = ""
                self._main()

            def _main(self):
                self.resizable(True, True)
                self.geometry("800x600")
                self.mc2 = mc.get() + ".py"
                path = os.getcwd()
                for n in os.listdir(path):
                    if self.mc2 == n:
                        self.mc2 = self.mc2+"(有同名文件，已自动更改名称).py"
                self.title(self.mc2)
                from tkinter import Canvas
                self.edit_frame = Canvas(self, height=600, width=800,
                                         bg="white", highlightthickness=0)
                self.edit_frame.pack()
                from tkinter import Text
                self.line_text = Text(self.edit_frame, width=7, height=600, spacing3=5,
                                      bg="#DCDCDC", bd=0, font=(zt, 14), takefocus=0, state="disabled",
                                      cursor="arrow")
                self.line_text.pack(side="left", expand=True)
                self.update()
                self.text = scrolledtext.ScrolledText(self.edit_frame, height=1, wrap="none", spacing3=5,
                                                      width=self.winfo_width() - self.line_text.winfo_width(),
                                                      bg="white",
                                                      bd=0, font=(zt, 14), undo=True, insertwidth=1)

                # 代码补全=====================
                def bqzt(event):
                    import random
                    import os
                    hcpath = os.getcwd() + "\\缓存文件（删除了不会造成影响）"
                    #hcpath = repr(hcpath_no)
                    while True:
                        try:
                            import os
                            name = os.listdir(hcpath)
                            self.mc3 = str(random.randint(1, 10000000000000000000000000000000000000000))
                            if self.mc3 not in name:
                                break
                        except:
                            self.mc3 = str(random.randint(1, 10000000000000000000000000000000000000000))
                            break

                    lj = os.getcwd()
                    try:
                        os.mkdir(lj + "\\缓存文件（删除了不会造成影响）")
                        self.mc3 = "缓存文件（删除了不会造成影响）//" + self.mc3
                    except:
                        self.mc3 = "缓存文件（删除了不会造成影响）//" + self.mc3

                    def bc():
                        a = self.text.get("1.0", "end")
                        with open(self.mc3, "w+", encoding="UTF-8") as file:
                            file.write(a)
                    bc()
                    # 创建函数列表
                    dmlist = []
                    #遍历文件获取代码库
                    # 读取配置
                    try:
                        with open("设置\\python.txt", "r", encoding="UTF-8") as file:
                            for line in file:
                                sb = len(line)
                                sb = sb + 1
                                sb2 = sb - 2
                                wbd = line[sb2:sb]
                                if wbd == "\n":
                                    line = line[0:sb2]
                                dmlist.append(line)
                    except:
                        dmlist = ["print",'def','class','import','from','if','and',"None","or",'==','!=','+=','-=','eles:','elif']
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
                    import linecache
                    text = linecache.getline(self.mc3, linenum2)
                    ftext = text[0:lie2]
                    print(ftext)  # 第一个输出内容，为切分后有可能是半代码的内容
                    # 利用分词，获取用户输入的那半个函数
                    import jieba
                    feilist = jieba.lcut(ftext)
                    print(feilist)  # 第二个输出，为切分后的列表

                    #智能补全系统
                    for i in range(1,linenum2):
                        import linecache
                        fxbl = linecache.getline(self.mc3,i)
                        if " = " in fxbl:
                            import jieba
                            yslist = jieba.lcut(fxbl)
                            dyfcdw = yslist.index("=")
                            dyfcdw = dyfcdw - 2
                            blm = yslist[dyfcdw]
                            dmlist.append(blm)
                        if "def " in fxbl:
                            import jieba
                            yslist = jieba.lcut(fxbl)
                            dyfcdw = yslist.index("def")
                            dyfcdw = dyfcdw + 2
                            blm = yslist[dyfcdw]
                            blm = blm + "()"
                            dmlist.append(blm)
                        if "class " in fxbl:
                            import jieba
                            yslist = jieba.lcut(fxbl)
                            dyfcdw = yslist.index("class")
                            dyfcdw = dyfcdw + 2
                            blm = yslist[dyfcdw]
                            blm = blm + "()"
                            dmlist.append(blm)

                    def power(n):
                        jian = n + n
                        far = n - jian
                        return far

                    a = 1
                    while True:
                        try:
                            if feilist[power(a)] == "\n":
                                a = a + 1
                            else:
                                print(feilist[power(a)])  # 第三个输出，为去除换行符后的内容
                                bandm = feilist[power(a)]
                                break
                        except:
                            bandm = "   "
                            break

                    #智能符号补全
                    #插入符号
                    def crfh(fh):
                        fz(fh)
                        def zt(event=None):
                            global root
                            self.text.event_generate('<<Paste>>')
                        zt()
                        self.text.mark_set("insert", "%d.%d" % (linenum2, lie2))
                    if bandm == '"':
                        crfh('"')
                    elif bandm == "'":
                        crfh("'")
                    elif bandm == "(":
                        crfh(")")
                    elif bandm == "[":
                        crfh("]")
                    elif bandm == "{":
                        crfh("}")
                    else:
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
                        print(hx)  # 最后一个输出，推荐列表

                        # 插入组件
                        def cr(bandm, xzdm):  # bandm用户输入的那一半代码，xzdm用户选择的代码
                            bancd = len(bandm)
                            xzcd = len(xzdm)
                            bqdm = xzdm[bancd:xzcd]
                            fz(bqdm)

                            def zt(event=None):
                                global root
                                self.text.event_generate('<<Paste>>')

                            zt()

                        # 补全弹窗
                        win = Toplevel()
                        win.overrideredirect(True)
                        win.wm_attributes('-topmost', 1)

                        def fuck():
                            win.destroy()

                        def fuck2(event):
                            win.destroy()

                        win.after(10000, fuck)
                        x = win.winfo_pointerx() - 1
                        y = win.winfo_pointery() - 1
                        x2 = str(x)
                        y2 = str(y)
                        hxs = len(hx)
                        if hxs > 6:
                            k = 132
                        else:
                            k = hxs * 21
                        k2 = str(k)
                        ckdx = "100x" + k2
                        weizhi = ckdx + "+" + x2 + "+" + y2
                        win.geometry(weizhi)
                        sc = t.Scrollbar(win, bootstyle=sjgdtys())
                        sc.pack(side=RIGHT, fill=Y)
                        hxlist = Listbox(win, yscrollcommand=sc.set)
                        hxlist.pack(expand=True)
                        hxlist.selection_set(first=0)
                        # 滚动条动，列表跟着动
                        sc.config(command=hxlist.yview)
                        if hx == ["无建议"]:
                            hxlist.insert(END, "无建议")
                            win.bind("<Alt_R>", fuck2)
                            win.bind("<Alt_L>", fuck2)
                        else:
                            for item in hx:
                                hxlist.insert(END, item)  # END表示每插入一个都是在最后一个位置

                            def crzb(event):
                                for i in hxlist.curselection():
                                    cr(bandm, hxlist.get(i))
                                    win.destroy()

                            win.bind("<Return>", crzb)
                            win.bind("<Double-Button-1>", crzb)
                            win.bind("<Alt_R>",fuck2)
                            win.bind("<Alt_L>",fuck2)
                        win.mainloop()

                self.text.bind("<Alt_L>", bqzt)
                self.text.bind("<Alt_R>", bqzt)
                # 代码补全底======================


                #自动缩进
                self.text.bind("<Return>", self.enter)
                #======

                #缩进规范
                def tab(event):
                    self.text.insert('insert', '    ')
                    self.get_txt_thread()
                self.text.bind("<Tab>",tab)
                #======

                self.text.vbar.configure(command=self.scroll)
                self.text.pack(side="left", fill="both")
                self.line_text.bind("<MouseWheel>", self.wheel)
                self.text.bind("<MouseWheel>", self.wheel)
                self.text.bind("<Control-v>", lambda e: self.get_txt_thread())
                self.text.bind("<Control-V>", lambda e: self.get_txt_thread())
                self.text.bind("<Key>", lambda e: self.get_txt_thread())
                self.show_line()
                #代码高亮（text后）
                if ColorDelegator:
                    colorobj = None
                    # 设置代码高亮显示
                    _codefilter = ColorDelegator()

                    def defines():
                        dics = {"foreground": "", "background": "#010c07"}
                        self = _codefilter
                        # window.text = text
                        # auto = autocomplete.AutoComplete(window)
                        self.tagdefs = {
                            "COMMENT": {"foreground": "green", "background": "#010c07"},
                            "KEYWORD": {"foreground": "blue", "background": "#010c07"},
                            "BUILTIN": {"foreground": "gray", "background": "#010c07"},
                            "STRING": {"foreground": "green", "background": "#010c07"},
                            "DEFINITION": {"foreground": "purple", "background": "#010c07"},
                            "SYNC": {'background': "#010c07", 'foreground': "red"},
                            "TODO": {'background': "#010c07", 'foreground': "red"},
                            "ERROR": {"foreground": "red", "background": "#010c07"},
                            # The following is used by ReplaceDialog:
                            "hit": {"foreground": None, "background": "#010c07"},
                        }

                        # if DEBUG: print('tagdefs', self.tagdefs)

                    _codefilter.LoadTagDefs = defines
                    if not colorobj:
                        colorobj = Percolator(self.text)#Text名称
                    colorobj.insertfilter(_codefilter)
                    #代码高亮（text后）

                if not autocomplete:
                    pass
                else:
                    self.text = self.text
                    auto = autocomplete.AutoComplete(self)

                def yxjb():
                    a = self.text.get("1.0","end")
                    with open(self.mc2,"w",encoding="UTF-8") as file:
                        file.write(a)
                    #读取配置
                    try:
                        with open("设置\\jsq.txt", "r", encoding="UTF-8") as file:
                            jsqaa = file.read()
                            jsqxz = jsqaa
                    except:
                        jsqxz = "F"
                    ###
                    if jsqxz == "F":
                        dm = "python -i "+self.mc2
                    else:
                        with open("设置\\jsqpath.txt", "r", encoding="UTF-8") as file:
                            pathjsq = file.read()
                        dm = pathjsq + " -i " + self.mc2
                    os.system(dm)

                def yx():
                    from threading import Thread
                    t2 = Thread(target=yxjb)
                    t2.start()

                def bc():
                    a = self.text.get("1.0", "end")
                    with open(self.mc2,"w",encoding="UTF-8") as file:
                        file.write(a)

                # 自动保存
                # 读取用户设置
                try:
                    with open("设置\\zdbc.txt", "r", encoding="UTF-8") as file:
                        zd = file.read()
                        bcsz = zd
                except:
                    bcsz = "F"
                if bcsz == "T":
                    def zdbc(event):
                        a = self.text.get("1.0", "end")
                        with open(self.mc2,"w",encoding="UTF-8") as file:
                            file.write(a)
                    self.bind("<Key>", zdbc)
                # 自动保存

                #示例代码
                texts = i
                self.text.insert(1.0, texts)
                self.get_txt_thread()
                #按钮
                # Button(self.edit_frame,text="运行程序",command=yx,fg=ztys).pack(side=RIGHT)
                # Button(self.edit_frame, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
                # Button(self.edit_frame, text="库管理", command=kgl,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="代码提示", command=dmts,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="更多插件", command=cj,fg=ztys).pack(side=LEFT)
                # Button(self, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
                def cmd():
                    os.startfile("cmd")


                def cx():
                    self.text.edit_undo()

                def hf():
                    self.text.edit_redo()

                #搜索系统===========================================================
                def Init():
                    global text

                    x = self.text.get("1.0", END)
                    self.text.delete("1.0", END)
                    # 重新插入文本
                    self.text.insert(INSERT, x)

                def fun():
                    '查找所有满足条件的字符串'
                    global x, li
                    start = "1.0"
                    while True:
                        pos = self.text.search(x, start, stopindex=END)
                        if not pos:  # 没有找到
                            # if len(li) != 0:
                            # print li
                            break
                        li.append(pos)
                        # len(x) 避免一个字符被查找多次
                        start = pos + "+%dc" % len(x)

                # num 设置当前要显示的是第几个
                self.num = 0
                # 用于查看当前输入的字符串和之前的字符串是否相同，如果相同的话，则要从第一个开始查找，初始化num的值
                self.str1 = ""
                self.str2 = ""

                def find1():
                    global x, li, num, text, str1, str2
                    li = []
                    Init()
                    x = self.e1.get()
                    if len(x) == 0:
                        showerror('错误', '请输入内容')
                        return

                    str1 = x
                    # 如果说当前的str1是新输入的，则num要从0开始查找
                    if self.str2 != self.str1:
                        self.num = 0
                    # 用现在的值把之前的值覆盖
                    self.str2 = self.str1
                    fun()
                    if len(li) == 0:
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    if self.num == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                        showinfo("查找结束", "找不到%s了" % x)
                        self.num = 0
                        return
                    # 获取当前颜色要变化的位置
                    i = li[self.num]
                    self.num += 1

                    Init()
                    k, t = i.split(".")
                    t = str(len(x) + int(t))
                    j = k + '.' + t
                    self.text.tag_add("tag1", i, j)
                    self.text.tag_config("tag1", background="yellow", foreground="blue")
                    self.text.see(i)
                    li = []

                def find2():
                    global x, li, num, text, str1, str2
                    li = []
                    Init()
                    x = self.e2.get()
                    if len(x) == 0:
                        showerror('错误', '请输入内容')
                        return

                    self.str1 = x
                    # 如果说当前的str1是新输入的，则num要从-1开始查找
                    if self.str2 != self.str1:
                        num = -1
                    # 用现在的值把之前的值覆盖
                    self.str2 = self.str1
                    fun()
                    if len(li) == 0:
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    if abs(num + 1) == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                        showinfo("查找结束", "找不到%s了" % x)
                        self.num = -1
                        return
                    # 获取当前颜色要变化的位置
                    i = li[self.num]
                    self.num -= 1

                    Init()
                    k, t = i.split(".")
                    t = str(len(x) + int(t))
                    j = k + '.' + t
                    self.text.tag_add("tag1", i, j)
                    self.text.tag_config("tag1", background="yellow", foreground="blue")
                    self.text.see(i)
                    li = []

                def find3():
                    global x, li
                    # 每次进行一次全部查找，一定要先把li列表初始化
                    li = []
                    Init()
                    x = self.e3.get()
                    if len(x) == 0:  # 如果说从输入框中得不到内容，则直接终止，不进行判断
                        showerror("错误", "请输入内容")
                        return
                    fun()
                    if len(li) == 0:  # 没有找到，直接终止即可
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    for i in li:
                        k, t = i.split(".")
                        # 加上字符串的长度，即判断能达到的位置
                        t = str(len(x) + int(t))
                        # 重新连接
                        j = k + '.' + t
                        # 加特殊的前景色和背景色
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                    li = []

                def change():
                    global top, text
                    # 如果要关闭窗口，则获取Text组件中的所有文本，
                    # 再重新输入，防止查找的结果对Text文本框产生影响，然后关闭即可
                    Init()
                    # 刷新，关闭顶层窗口
                    top.withdraw()

                # Entry框
                e1 = 0
                e2 = 0
                e3 = 0

                x = 0
                li = []
                top = 0

                def create():
                    global e1, e2, e3, top
                    top = Toplevel()
                    top.title("查找")
                    # 设置顶层窗口的大小不可变
                    # top.maxsize(250, 110)
                    # top.minsize(250, 110)

                    # 两个按钮和两个Entry输入框
                    self.e1 = t.Entry(top,bootstyle=sjys())
                    self.e1.grid(row=0, column=0)
                    t.Button(top, text="查找下一个", width=10, command=find1,bootstyle=sjanys()).grid(row=0, column=1)
                    self.e2 = t.Entry(top,bootstyle=sjys())
                    self.e2.grid(row=1, column=0)
                    t.Button(top, text="查找上一个", width=10, command=find2,bootstyle=sjanys()).grid(row=1, column=1)
                    self.e3 = t.Entry(top,bootstyle=sjys())
                    self.e3.grid(row=2, column=0)
                    t.Button(top, text="查找全部", width=10, command=find3,bootstyle=sjanys()).grid(row=2, column=1)

                    # 当顶层窗口关闭的时候，所有的设置还原
                    top.protocol(name='WM_DELETE_WINDOW', func=change)
                #===================================================================================

                #替换===============================================================
                def replace():
                    """替换"""
                    self.coding = StringVar(self)
                    replace_dlg = ReplaceDialog(self,self.text)
                    # replace_dlg.attributes("-topmost", True)
                    replace_dlg.show()
                #==================================================================


                menu = Menu(self, tearoff=0)
                menu.add_command(label="运行代码",command=yx)
                menu.add_command(label="保存文件",command=bc)
                menu.add_command(label="撤销", command=cx)
                menu.add_command(label="恢复", command=hf)
                menu.add_command(label="搜索", command=create)
                menu.add_command(label="替换", command=replace)
                menu.add_command(label="库管理",command=kgl)
                menu.add_command(label="背景音乐",command=yy)
                menu.add_command(label="代码补全",command=dmts)
                menu.add_command(label="更多插件",command=cj)
                menu.add_command(label="终端",command=cmd)



                def popupmenu(event):
                    menu.post(event.x_root, event.y_root)


                self.config(menu=menu)
                self.bind("<Button-3>", popupmenu)

            #自动缩进
            def enter(self, *args):
                self.i = 0
                a = self.text.index('insert')
                a = float(a)
                aa = int(a)
                b = self.text.get(float(aa), a).replace('\n', '')
                c = b
                if b[-1:] == ':':
                    i = 0
                    while True:
                        if b[:4] == '    ':
                            b = b[4:]
                            i += 1
                        else:
                            break
                    self.i = i + 1
                else:
                    i = 0
                    while True:
                        if b[:4] == '    ':
                            b = b[4:]
                            i += 1
                        else:
                            break
                    self.i = i
                    if c.strip() == 'break' or c.strip() == 'return' or c.strip() == 'pass' or c.strip() == 'continue':
                        self.i -= 1
                self.text.insert('insert', '\n')
                for j in range(self.i):
                    self.text.insert('insert', '    ')
                self.get_txt_thread()
                return 'break'

            def wheel(self, event):
                self.line_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"

            def scroll(self, *xy):
                self.line_text.yview(*xy)
                self.text.yview(*xy)

            def get_txt_thread(self):
                Thread(target=self.get_txt).start()

            def get_txt(self):
                self.thread_lock.acquire()
                if self.txt != self.text.get("1.0", "end")[:-1]:
                    self.txt = self.text.get("1.0", "end")[:-1]
                    self.show_line()
                else:
                    self.thread_lock.release()

            def show_line(self):
                sb_pos = self.text.vbar.get()
                self.line_text.configure(state="normal")
                self.line_text.delete("1.0", "end")
                txt_arr = self.txt.split("\n")
                if len(txt_arr) == 1:
                    self.line_text.insert("1.1", " 1")
                else:
                    for i in range(1, len(txt_arr) + 1):
                        self.line_text.insert("end", " " + str(i))
                        if i != len(txt_arr):
                            self.line_text.insert("end", "\n")
                if len(sb_pos) == 4:
                    self.line_text.yview_moveto(0.0)
                elif len(sb_pos) == 2:
                    self.line_text.yview_moveto(sb_pos[0])
                    self.text.yview_moveto(sb_pos[0])
                self.line_text.configure(state="disabled")
                try:
                    self.thread_lock.release()
                except RuntimeError:
                    pass


        run = Main()
        run.mainloop()

        # # 主窗口
        # mc2 = mc.get() + ".py"
        # window = Tk()
        # window.title(mc2)
        #
        # # 设置text
        # text = Text(window, font=zt, fg=fg,undo = True)
        # scroll = Scrollbar(window)
        # # 放到窗口的右侧, 填充Y竖直方向
        # scroll.pack(side=RIGHT, fill=Y)
        #
        # # 两个控件关联
        # scroll.config(command=text.yview)
        # text.config(yscrollcommand=scroll.set)
        #
        # text.pack(fill=BOTH, expand=1)
        #
        #
        # #代码高亮（text后）
        # if ColorDelegator:
        #     colorobj = None
        #     # 设置代码高亮显示
        #     _codefilter = ColorDelegator()
        #
        #     def defines():
        #         dics = {"foreground": "", "background": "white"}
        #         self = _codefilter
        #         # window.text = text
        #         # auto = autocomplete.AutoComplete(window)
        #         self.tagdefs = {
        #             "COMMENT": {"foreground": "green", "background": "white"},
        #             "KEYWORD": {"foreground": "blue", "background": "white"},
        #             "BUILTIN": {"foreground": "gray", "background": "white"},
        #             "STRING": {"foreground": "green", "background": "white"},
        #             "DEFINITION": {"foreground": "purple", "background": "white"},
        #             "SYNC": {'background': "pink", 'foreground': "red"},
        #             "TODO": {'background': "pink", 'foreground': "red"},
        #             "ERROR": {"foreground": "red", "background": "white"},
        #             # The following is used by ReplaceDialog:
        #             "hit": {"foreground": None, "background": "white"},
        #         }
        #
        #         # if DEBUG: print('tagdefs', self.tagdefs)
        #
        #     _codefilter.LoadTagDefs = defines
        #     if not colorobj:
        #         colorobj = Percolator(text)#Text名称
        #     colorobj.insertfilter(_codefilter)
        #     #代码高亮（text后）
        #
        # if not autocomplete:
        #     pass
        # else:
        #     window.text = text
        #     auto = autocomplete.AutoComplete(window)
        #
        #
        # def yx():
        #     a = text.get("1.0","end")
        #     with open(mc2,"w",encoding="UTF-8") as file:
        #         file.write(a)
        #     dm = "python -i "+mc2
        #     os.system(dm)
        #
        # def bc():
        #     a = text.get("1.0", "end")
        #     with open(mc2,"w",encoding="UTF-8") as file:
        #         file.write(a)
        # #示例代码
        # texts = i
        # text.insert(1.0, texts)
        # #按钮
        # Button(window,text="运行程序",command=yx,fg=ztys).pack(side=RIGHT)
        # Button(window, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
        # Button(window, text="库管理", command=kgl,fg=ztys).pack(side=LEFT)
        # Button(window, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
        # Button(window, text="代码提示", command=dmts,fg=ztys).pack(side=LEFT)
        # Button(window, text="更多插件", command=cj,fg=ztys).pack(side=LEFT)
        # def cmd():
        #     os.startfile("cmd")
        # Button(window, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
        #
        # def cx():
        #     text.edit_undo()
        #
        # def hf():
        #     text.edit_redo()
        #
        #
        # menu = Menu(window, tearoff=0)
        # menu.add_command(label="撤销", command=cx)
        # menu.add_separator()
        # menu.add_command(label="恢复", command=hf)
        # menu.add_separator()
        #
        # def popupmenu(event):
        #     menu.post(event.x_root, event.y_root)
        #
        # window.bind("<Button-3>", popupmenu)
        #
        # window.mainloop()

    t.Button(zck,text="创建文件",command=xjbc,bootstyle=sjanys()).pack()

    zck.mainloop()

ihtml = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>欢迎使用奥利给HTML编译器</title>
</head>
<body>
<p>Hello,欢迎使用奥利给HTML编译器</p>
</body>
</html>
'''

def dmtshtml():  # 代码提示
    win = Toplevel()
    canvas = Canvas(win, width=200, height=310000, scrollregion=(0, 0, 820, 2050))  # 创建canvas
    dmts = Frame(canvas, height=100)  # 用框架换掉窗口，方便滚动
    win.title("代码提示")
    win.geometry("300x300")
    # sb = Scrollbar(dmts)
    # sb.pack(side=RIGHT, fill=Y)
    # 这个scrollbar没有用了，看下面那个

    # 标准节
    # Label(dmts, text="print()，输出").pack()
    # def dm():
    #     fz("print()")
    # Button(dmts, text="复制代码", command=dm).pack()
    # 已上为标准节
    for i in range(4):
        Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()

    def dmdq():
        dkwy("https://algfwq.lanzoub.com/iqi3n04hqq7g")

    Label(dmts, text="代码提示", font=20).pack()
    Label(dmts, text="点击按钮复制代码").pack()
    t.Button(dmts,text="代码大全,提取码alg",command=dmdq,bootstyle=sjanys()).pack()
    bzj(dmts,"<HTML></HTML>,文件类型","<HTML></HTML>")
    bzj(dmts,"<TITLE></TITLE>,文件主题","<TITLE></TITLE>")
    bzj(dmts,"<HEAD></HEAD>,文头","<HEAD></HEAD>")
    bzj(dmts,"<BODY></BODY>,文体","<BODY></BODY>")
    bzj(dmts,"<H?></H?>,标题","<H?></H?>")
    bzj(dmts,"<DIV></DIV>,区分","<DIV></DIV>")
    bzj(dmts,"<BLOCKQUOTE></BLOCKQUOTE>,引文区块","<BLOCKQUOTE></BLOCKQUOTE>")
    bzj(dmts,"<EM></EM>,强调","<EM></EM>")
    bzj(dmts,"<STRONG></STRONG>特别强调","<STRONG></STRONG>")
    bzj(dmts,"<CITE></CITE>引文",'<CITE></CITE>')
    bzj(dmts,'<CODE></CODE>码','<CODE></CODE>')
    bzj(dmts,'<KBD></KBD>键盘输入','<KBD></KBD>')
    bzj(dmts,"<BIG></BIG>大字","<BIG></BIG>")
    bzj(dmts,'<SMALL></SMALL>小字','<SMALL></SMALL>')
    bzj(dmts,'加粗 <B></B>','<B></B>')
    bzj(dmts,'斜体 <I></I>','<I></I>')


    vbar = t.Scrollbar(win, orient=VERTICAL, command=canvas.yview,bootstyle=sjgdtys())  # 竖直滚动条
    #vbar.place(x=280, y=0, height=300)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.config(yscrollcommand=vbar.set)
    dmts.pack()  # 显示控件
    canvas.pack()
    canvas.create_window((90, 240), window=dmts)  # create_window,让他们互相绑定
    win.mainloop()

def xjwjHTML():
    zck = Toplevel()
    zck.title("新建文件")
    zck.geometry("250x250")
    Label(zck,text="请输入文件名称",font=20).pack()
    Label(zck, text="不用加后缀", font=20).pack()
    mc = t.Entry(zck,bootstyle=sjys())
    mc.pack()
    def xjbc():
        from tkinter import scrolledtext
        from threading import Thread, RLock

        class Main(Toplevel):
            def __init__(self):
                super().__init__()
                self.thread_lock = RLock()
                self.txt = ""
                self._main()

            def _main(self):
                self.resizable(True, True)
                self.geometry("800x600")
                self.mc2 = mc.get() + ".html"
                path = os.getcwd()
                for n in os.listdir(path):
                    if self.mc2 == n:
                        self.mc2 = self.mc2 + "(有同名文件，已自动更改名称).html"
                self.title(self.mc2)
                from tkinter import Canvas
                self.edit_frame = Canvas(self, height=600, width=800,
                                         bg="white", highlightthickness=0)
                self.edit_frame.pack()
                from tkinter import Text
                self.line_text = Text(self.edit_frame, width=7, height=600, spacing3=5,
                                      bg="#DCDCDC", bd=0, font=(zt, 14), takefocus=0, state="disabled",
                                      cursor="arrow")
                self.line_text.pack(side="left", expand=True)
                self.update()
                self.text = scrolledtext.ScrolledText(self.edit_frame, height=1, wrap="none", spacing3=5,
                                                      width=self.winfo_width() - self.line_text.winfo_width(),
                                                      bg="white",
                                                      bd=0, font=(zt, 14), undo=True, insertwidth=1)

                #代码补全头
                from idlelib.autocomplete import AutoComplete
                def dmbq():
                    AutoComplete(editwin=self)
                #代码补全底

                # 缩进规范
                def tab(event):
                    self.text.insert('insert', '    ')
                    self.get_txt_thread()

                self.text.bind("<Tab>", tab)
                # ======

                self.text.vbar.configure(command=self.scroll)
                self.text.pack(side="left", fill="both")
                self.line_text.bind("<MouseWheel>", self.wheel)
                self.text.bind("<MouseWheel>", self.wheel)
                self.text.bind("<Control-v>", lambda e: self.get_txt_thread())
                self.text.bind("<Control-V>", lambda e: self.get_txt_thread())
                self.text.bind("<Key>", lambda e: self.get_txt_thread())
                self.show_line()

                #代码高亮（text后）
                if ColorDelegator:
                    colorobj = None
                    # 设置代码高亮显示
                    _codefilter = ColorDelegator()

                    def defines():
                        dics = {"foreground": "", "background": "white"}
                        self = _codefilter
                        # window.text = text
                        # auto = autocomplete.AutoComplete(window)
                        self.tagdefs = {
                            "COMMENT": {"foreground": "green", "background": "white"},
                            "KEYWORD": {"foreground": "blue", "background": "white"},
                            "BUILTIN": {"foreground": "gray", "background": "white"},
                            "STRING": {"foreground": "green", "background": "white"},
                            "DEFINITION": {"foreground": "purple", "background": "white"},
                            "SYNC": {'background': "pink", 'foreground': "red"},
                            "TODO": {'background': "pink", 'foreground': "red"},
                            "ERROR": {"foreground": "red", "background": "white"},
                            # The following is used by ReplaceDialog:
                            "hit": {"foreground": None, "background": "white"},
                        }

                        # if DEBUG: print('tagdefs', self.tagdefs)

                    _codefilter.LoadTagDefs = defines
                    if not colorobj:
                        colorobj = Percolator(self.text)#Text名称
                    colorobj.insertfilter(_codefilter)
                    #代码高亮（text后）

                if not autocomplete:
                    pass
                else:
                    self.text = self.text
                    auto = autocomplete.AutoComplete(self)


                def yxjb():
                    a = self.text.get("1.0","end")
                    with open(self.mc2,"w",encoding="UTF-8") as file:
                        file.write(a)
                    dm = self.mc2
                    os.system(dm)


                def yx():
                    from threading import Thread
                    t2 = Thread(target=yxjb)
                    t2.start()

                def bc():
                    a = self.text.get("1.0", "end")
                    with open(self.mc2,"w",encoding="UTF-8") as file:
                        file.write(a)

                # 自动保存
                # 读取用户设置
                try:
                    with open("设置\\zdbc.txt", "r", encoding="UTF-8") as file:
                        zd = file.read()
                        bcsz = zd
                except:
                    bcsz = "F"
                if bcsz == "T":
                    def zdbc(event):
                        a = self.text.get("1.0", "end")
                        with open(self.mc2, "w", encoding="UTF-8") as file:
                            file.write(a)

                    self.bind("<Key>", zdbc)
                # 自动保存

                #示例代码
                texts = ihtml
                self.text.insert(1.0, texts)
                self.get_txt_thread()
                #按钮
                # Button(self.edit_frame,text="运行程序",command=yx,fg=ztys).pack(side=RIGHT)
                # Button(self.edit_frame, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
                # Button(self.edit_frame, text="库管理", command=kgl,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="代码提示", command=dmts,fg=ztys).pack(side=LEFT)
                # Button(self.edit_frame, text="更多插件", command=cj,fg=ztys).pack(side=LEFT)
                # Button(self, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
                def cmd():
                    os.startfile("cmd")


                def cx():
                    self.text.edit_undo()

                def hf():
                    self.text.edit_redo()

                # 搜索系统===========================================================
                def Init():
                    global text

                    x = self.text.get("1.0", END)
                    self.text.delete("1.0", END)
                    # 重新插入文本
                    self.text.insert(INSERT, x)

                def fun():
                    '查找所有满足条件的字符串'
                    global x, li
                    start = "1.0"
                    while True:
                        pos = self.text.search(x, start, stopindex=END)
                        if not pos:  # 没有找到
                            # if len(li) != 0:
                            # print li
                            break
                        li.append(pos)
                        # len(x) 避免一个字符被查找多次
                        start = pos + "+%dc" % len(x)

                # num 设置当前要显示的是第几个
                self.num = 0
                # 用于查看当前输入的字符串和之前的字符串是否相同，如果相同的话，则要从第一个开始查找，初始化num的值
                self.str1 = ""
                self.str2 = ""

                def find1():
                    global x, li, num, text, str1, str2
                    li = []
                    Init()
                    x = self.e1.get()
                    if len(x) == 0:
                        showerror('错误', '请输入内容')
                        return

                    str1 = x
                    # 如果说当前的str1是新输入的，则num要从0开始查找
                    if self.str2 != self.str1:
                        self.num = 0
                    # 用现在的值把之前的值覆盖
                    self.str2 = self.str1
                    fun()
                    if len(li) == 0:
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    if self.num == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                        showinfo("查找结束", "找不到%s了" % x)
                        self.num = 0
                        return
                    # 获取当前颜色要变化的位置
                    i = li[self.num]
                    self.num += 1

                    Init()
                    k, t = i.split(".")
                    t = str(len(x) + int(t))
                    j = k + '.' + t
                    self.text.tag_add("tag1", i, j)
                    self.text.tag_config("tag1", background="yellow", foreground="blue")
                    self.text.see(i)
                    li = []

                def find2():
                    global x, li, num, text, str1, str2
                    li = []
                    Init()
                    x = self.e2.get()
                    if len(x) == 0:
                        showerror('错误', '请输入内容')
                        return

                    self.str1 = x
                    # 如果说当前的str1是新输入的，则num要从-1开始查找
                    if self.str2 != self.str1:
                        num = -1
                    # 用现在的值把之前的值覆盖
                    self.str2 = self.str1
                    fun()
                    if len(li) == 0:
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    if abs(num + 1) == len(li):  # 如果后面没有要查找的，则直接跳转到第一个继续
                        showinfo("查找结束", "找不到%s了" % x)
                        self.num = -1
                        return
                    # 获取当前颜色要变化的位置
                    i = li[self.num]
                    self.num -= 1

                    Init()
                    k, t = i.split(".")
                    t = str(len(x) + int(t))
                    j = k + '.' + t
                    self.text.tag_add("tag1", i, j)
                    self.text.tag_config("tag1", background="yellow", foreground="blue")
                    self.text.see(i)
                    li = []

                def find3():
                    global x, li
                    # 每次进行一次全部查找，一定要先把li列表初始化
                    li = []
                    Init()
                    x = self.e3.get()
                    if len(x) == 0:  # 如果说从输入框中得不到内容，则直接终止，不进行判断
                        showerror("错误", "请输入内容")
                        return
                    fun()
                    if len(li) == 0:  # 没有找到，直接终止即可
                        showinfo("查找结果", "没有要查询的结果")
                        return
                    for i in li:
                        k, t = i.split(".")
                        # 加上字符串的长度，即判断能达到的位置
                        t = str(len(x) + int(t))
                        # 重新连接
                        j = k + '.' + t
                        # 加特殊的前景色和背景色
                        self.text.tag_add("tag1", i, j)
                        self.text.tag_config("tag1", background="yellow", foreground="blue")
                    li = []

                def change():
                    global top, text
                    # 如果要关闭窗口，则获取Text组件中的所有文本，
                    # 再重新输入，防止查找的结果对Text文本框产生影响，然后关闭即可
                    Init()
                    # 刷新，关闭顶层窗口
                    top.withdraw()

                # Entry框
                e1 = 0
                e2 = 0
                e3 = 0

                x = 0
                li = []
                top = 0

                def create():
                    global e1, e2, e3, top
                    top = Toplevel()
                    top.title("查找")
                    # 设置顶层窗口的大小不可变
                    # top.maxsize(250, 110)
                    # top.minsize(250, 110)

                    # 两个按钮和两个Entry输入框
                    self.e1 = t.Entry(top, bootstyle=sjys())
                    self.e1.grid(row=0, column=0)
                    t.Button(top, text="查找下一个", width=10, command=find1, bootstyle=sjanys()).grid(row=0, column=1)
                    self.e2 = t.Entry(top, bootstyle=sjys())
                    self.e2.grid(row=1, column=0)
                    t.Button(top, text="查找上一个", width=10, command=find2, bootstyle=sjanys()).grid(row=1, column=1)
                    self.e3 = t.Entry(top, bootstyle=sjys())
                    self.e3.grid(row=2, column=0)
                    t.Button(top, text="查找全部", width=10, command=find3, bootstyle=sjanys()).grid(row=2, column=1)

                    # 当顶层窗口关闭的时候，所有的设置还原
                    top.protocol(name='WM_DELETE_WINDOW', func=change)
                # ===================================================================================

                # 替换===============================================================
                def replace():
                    """替换"""
                    self.coding = StringVar(self)
                    replace_dlg = ReplaceDialog(self, self.text)
                    # replace_dlg.attributes("-topmost", True)
                    replace_dlg.show()
                # ==================================================================

                menu = Menu(self, tearoff=0)
                menu.add_command(label="运行代码",command=yx)
                menu.add_command(label="保存文件",command=bc)
                menu.add_command(label="撤销", command=cx)
                menu.add_command(label="恢复", command=hf)
                menu.add_command(label="搜索", command=create)
                menu.add_command(label="替换", command=replace)
                menu.add_command(label="背景音乐",command=yy)
                menu.add_command(label="代码提示",command=dmtshtml)
                menu.add_command(label="更多插件",command=cj)
                menu.add_command(label="终端",command=cmd)



                def popupmenu(event):
                    menu.post(event.x_root, event.y_root)


                self.config(menu=menu)
                self.bind("<Button-3>", popupmenu)

            def wheel(self, event):
                self.line_text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                self.text.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"

            def scroll(self, *xy):
                self.line_text.yview(*xy)
                self.text.yview(*xy)

            def get_txt_thread(self):
                Thread(target=self.get_txt).start()

            def get_txt(self):
                self.thread_lock.acquire()
                if self.txt != self.text.get("1.0", "end")[:-1]:
                    self.txt = self.text.get("1.0", "end")[:-1]
                    self.show_line()
                else:
                    self.thread_lock.release()

            def show_line(self):
                sb_pos = self.text.vbar.get()
                self.line_text.configure(state="normal")
                self.line_text.delete("1.0", "end")
                txt_arr = self.txt.split("\n")
                if len(txt_arr) == 1:
                    self.line_text.insert("1.1", " 1")
                else:
                    for i in range(1, len(txt_arr) + 1):
                        self.line_text.insert("end", " " + str(i))
                        if i != len(txt_arr):
                            self.line_text.insert("end", "\n")
                if len(sb_pos) == 4:
                    self.line_text.yview_moveto(0.0)
                elif len(sb_pos) == 2:
                    self.line_text.yview_moveto(sb_pos[0])
                    self.text.yview_moveto(sb_pos[0])
                self.line_text.configure(state="disabled")
                try:
                    self.thread_lock.release()
                except RuntimeError:
                    pass


        run = Main()
        run.mainloop()
    # def xjbc():
    #     # 主窗口
    #     mc2 = mc.get() + ".html"
    #     window = Tk()
    #     window.title(mc2)
    #     # 设置text
    #     #text = Text(window, width=80, height=30,font=zt,fg=fg)
    #     # 设置text
    #     text = Text(window, font=zt, fg=fg, undo=True)
    #     scroll = Scrollbar(window)
    #     # 放到窗口的右侧, 填充Y竖直方向
    #     scroll.pack(side=RIGHT, fill=Y)
    #
    #     # 两个控件关联
    #     scroll.config(command=text.yview)
    #     text.config(yscrollcommand=scroll.set)
    #
    #     text.pack(fill=BOTH, expand=1)
    #     def yx():
    #         a = text.get("1.0","end")
    #         with open(mc2,"w",encoding="UTF-8") as file:
    #             file.write(a)
    #         dm = mc2
    #         os.system(dm)
    #
    #     def bc():
    #         a = text.get("1.0", "end")
    #         with open(mc2,"w",encoding="UTF-8") as file:
    #             file.write(a)
    #     #示例代码
    #     texts = ihtmldm
    #     text.insert(1.0, texts)
    #
    #     # 代码高亮（text后）
    #     if ColorDelegator:
    #         colorobj = None
    #         # 设置代码高亮显示
    #         _codefilter = ColorDelegator()
    #
    #         def defines():
    #             dics = {"foreground": "", "background": "white"}
    #             self = _codefilter
    #             self.tagdefs = {
    #                 "COMMENT": {"foreground": "green", "background": "white"},
    #                 "KEYWORD": {"foreground": "blue", "background": "white"},
    #                 "BUILTIN": {"foreground": "gray", "background": "white"},
    #                 "STRING": {"foreground": "green", "background": "white"},
    #                 "DEFINITION": {"foreground": "purple", "background": "white"},
    #                 "SYNC": {'background': "pink", 'foreground': "red"},
    #                 "TODO": {'background': "pink", 'foreground': "red"},
    #                 "ERROR": {"foreground": "red", "background": "white"},
    #                 # The following is used by ReplaceDialog:
    #                 "hit": {"foreground": None, "background": "white"},
    #             }
    #
    #             # if DEBUG: print('tagdefs', self.tagdefs)
    #
    #         _codefilter.LoadTagDefs = defines
    #         if not colorobj:
    #             colorobj = Percolator(text)  # Text名称
    #         colorobj.insertfilter(_codefilter)
    #         # 代码高亮（text后）
    #
    #     #按钮
    #     Button(window,text="运行代码",command=yx,fg=ztys).pack(side=RIGHT)
    #     Button(window, text="保存代码", command=bc,fg=ztys).pack(side=RIGHT)
    #     Button(window, text="背景音乐", command=yy,fg=ztys).pack(side=LEFT)
    #     Button(window, text="代码提示", command=dmtshtml,fg=ztys).pack(side=LEFT)
    #     Button(window, text="更多插件", command=cj, fg=ztys).pack(side=LEFT)
    #     def cmd():
    #         os.startfile("cmd")
    #     Button(window, text="终端", command=cmd,fg=ztys).pack(side=LEFT)
    #
    #     def cx():
    #         text.edit_undo()
    #
    #     def hf():
    #         text.edit_redo()
    #
    #
    #     menu = Menu(window, tearoff=0)
    #     menu.add_command(label="撤销", command=cx)
    #     menu.add_separator()
    #     menu.add_command(label="恢复", command=hf)
    #     menu.add_separator()
    #
    #     def popupmenu(event):
    #         menu.post(event.x_root, event.y_root)
    #
    #     window.bind("<Button-3>", popupmenu)
    #     window.mainloop()
    t.Button(zck, text="创建文件", command=xjbc,bootstyle=sjanys()).pack()

    zck.mainloop()

def xjwj():
    xjwin = Toplevel()
    xjwin.title("新建文件")
    xjwin.geometry("250x250")
    canvas = Canvas(xjwin, width=200, height=200, scrollregion=(0, 0,0,400))  # 创建canvas
    xj = Frame(canvas, height=100)  # 用框架换掉窗口，方便滚动

    Label(xj, text="请选择代码语言", font=20).pack()
    #Radiobutton(xj, text="Python", command=xjwjpy).pack()
    t.Checkbutton(xj, text="Python", command=xjwjpy,bootstyle=sjys()).pack()
    Label(xj, text="使用时请确保已安装Python解释器").pack()
    t.Checkbutton(xj, text="HTML", command=xjwjHTML,bootstyle=sjys()).pack()
    Label(xj, text="使用时请确保已安装浏览器").pack()


    for i in range(15):
        Label(xj, text="").pack()

    vbar = t.Scrollbar(xjwin, orient=VERTICAL, command=canvas.yview,bootstyle=sjgdtys())  # 竖直滚动条
    # vbar.place(x=280, y=0, height=300)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.config(yscrollcommand=vbar.set)
    xj.pack()  # 显示控件
    canvas.pack()
    canvas.create_window((90, 240), window=xj)  # create_window,让他们互相绑定
    xjwin.mainloop()

def gxbb():
    import threading
    htgx = threading.Thread(target=gxbbjb)
    htgx.start()

def gxbbjb():
    #无需复制（上）
    try:
        with open("设置\\url.txt","r",encoding="UTF-8") as file:
            url2 = file.read()
            url = url2
    except:
        url = r"https://algfwq.github.io/GX/"

    def pqwybqnr(wz,bq):#爬取网页标签内容，wz=网址，bq=标签
        import requests
        import bs4
        import lxml
        # 请求网页
        #作答区域1：修改下一行的网址，改为自己要请求的网页地址
        url = wz
        #作答区域2：补充下一行代码，使用requests库中的get()函数，请求网页url
        try:
            res = requests.get(url)
            res.encoding = "UTF-8"
        except:
            import tkinter as t
            gx = t.Toplevel()
            gx.title("检测失败")
            Label(gx, text="检测失败，可能是因为网站更新，或网络问题，请稍后重试，可以联系QQ：3104374883 ！", font=("宋体", 20)).pack()
            gx.mainloop()
        # 选取数据
        soup = bs4.BeautifulSoup(res.text,"lxml")
        #作答区域3：查找soup中所有的a标签
        data = soup.find_all(bq)
        # 展示结果
        for n in data:
            return n.text

    bb = pqwybqnr(url,"h1")
    gxnr = pqwybqnr(url,"h2")
    xzwz = pqwybqnr(url,"h3")
    tqm = pqwybqnr(url,"h4")
    bb2 = float(bb)


    if bb2 > 3.0:
        def gxwj():
            def dkwy(wz):  # 打卡网址，wz=网址
                import webbrowser as w
                w.open(wz)
            dkwy(xzwz)
        import tkinter as t
        gx = t.Toplevel()
        gx.title("有可用更新")
        # Label(gx,text="有可用更新，请更新！",font=("宋体",20),fg=ztys).pack()
        # Label(gx,text="更新版本："+bb,font=("宋体",20),fg=ztys).pack()
        # Label(gx,text="更新内容："+gxnr,font=("宋体",20),fg=ztys).pack()
        # Label(gx,text="下载地址："+xzwz,font=("宋体",20),fg=ztys).pack()
        t = Text(gx,font=("宋体",15),fg=ztys,height=10)
        t.pack(fill=BOTH, expand=1)
        t.insert(END,"有可用更新，请更新！\n")
        t.insert(END,"更新版本："+bb+"\n")
        t.insert(END,"更新内容："+gxnr+"\n")
        t.insert(END,"下载地址："+xzwz+"\n")
        t.insert(END,"提取码："+tqm+"\n")

        Button(gx, text="立刻更新", command=gxwj).pack()
        gx.mainloop()
    else:
        import tkinter as t
        gx = t.Toplevel()
        gx.title("无可用更新")
        Label(gx, text="无可用更新，请继续使用！", font=("宋体",20)).pack()
        gx.mainloop()

#关于
def gy():
    win = Toplevel()
    win.title("关于")
    win.geometry("300x300")
    Label(win,text="关于",font=("kaiti",30)).pack()
    Label(win,text="奥利给开发者编译器\n由奥利给硬件科技工作室制作",font=20).pack()
    Label(win,text="版本：3.0",font=20).pack()
    win.mainloop()
#重启程序
def cq():
    import sys
    import os
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, *sys.argv)
#设置
def gxsz():
    szdy = Toplevel()
    szdy.title("设置")
    szdy.geometry("250x250")
    def zdbcsz():
        zdgx = Toplevel()
        zdgx.title("自动保存设置")
        zdgx.geometry("250x250")

        def zd():

            def bc():
                lj = os.getcwd()
                try:
                    os.mkdir(lj + "\\设置")
                    with open("设置\\zdbc.txt", "w", encoding="UTF-8") as file:
                        file.write("T")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                except:
                    with open("设置\\zdbc.txt", "w", encoding="UTF-8") as file:
                        file.write("T")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()

                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
            bc()
        def sd():

            def bc():
                lj = os.getcwd()
                try:
                    os.mkdir(lj + "\\设置")
                    with open("设置\\zdbc.txt", "w", encoding="UTF-8") as file:
                        file.write("F")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                except:
                    with open("设置\\zdbc.txt", "w", encoding="UTF-8") as file:
                        file.write("F")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()

            bc()

        t.Radiobutton(zdgx, text="启动自动保存", command=zd,bootstyle=sjys()).pack()
        t.Radiobutton(zdgx, text="启动手动保存", command=sd,bootstyle=sjys()).pack()
        zdgx.mainloop()
    def dmzt():
        ggzt = Toplevel()
        ggzt.title("更改代码颜色")
        ggzt.geometry("250x250")
        Label(ggzt,text="请输入颜色名称",font=("kaiti",20)).pack()
        # mc = Entry(ggzt)
        # mc.pack()
        mc = t.Combobox(ggzt,bootstyle=sjys())
        a = ["Navy","Aqua","Lime","Blue"]
        mc['values'] = a  # 设置下拉列表的值
        mc.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标值
        mc.pack()
        def bc():
            nr = mc.get()
            lj = os.getcwd()
            try:
                os.mkdir(lj + "\\设置")
                with open("设置\\fg.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
            except:
                with open("设置\\fg.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
        t.Button(ggzt, text="更改代码颜色",command=bc,bootstyle=sjanys()).pack()
        ggzt.mainloop()
    def ggzt():
        ggzt = Toplevel()
        ggzt.title("更改代码字体")
        ggzt.geometry("250x250")
        Label(ggzt,text="请输入字体名称",font=("kaiti",20)).pack()
        # mc = t.Entry(ggzt,bootstyle=sjys())
        # mc.pack()
        mc = t.Combobox(ggzt, bootstyle=sjys())
        a = ["kaiti", "宋体", "Consolas", "华文行楷"]
        mc['values'] = a  # 设置下拉列表的值
        mc.current(0)  # 设置下拉列表默认显示的值，0为 numberChosen['values'] 的下标值
        mc.pack()
        def bc():
            nr = mc.get()
            lj = os.getcwd()
            try:
                os.mkdir(lj+"\\设置")
                with open("设置\\zt.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
            except:
                with open("设置\\zt.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
        t.Button(ggzt, text="更改代码字体",command=bc,bootstyle=sjanys()).pack()
        ggzt.mainloop()
    def ys():
        ggzt = Toplevel()
        ggzt.title("更改字体颜色")
        ggzt.geometry("250x250")
        Label(ggzt, text="请输入颜色名称", font=("kaiti",20)).pack()
        mc = t.Entry(ggzt,bootstyle=sjys())
        mc.pack()
        def bc():
            nr = mc.get()
            lj = os.getcwd()
            try:
                os.mkdir(lj + "\\设置")
                with open("设置\\ztys.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
            except:
                with open("设置\\ztys.txt", "w", encoding="UTF-8") as file:
                    file.write(nr)
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
        Button(ggzt, text="更改字体颜色", command=bc,bootstyle=sjanys()).pack()
        ggzt.mainloop()
    def zdgx():
        zdgx = Toplevel()
        zdgx.title("更新设置")
        zdgx.geometry("250x250")
        def zd():
            def bc():
                lj = os.getcwd()
                try:
                    os.mkdir(lj + "\\设置")
                    with open("设置\\gx.txt", "w", encoding="UTF-8") as file:
                        file.write("自动")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                except:
                    with open("设置\\gx.txt", "w", encoding="UTF-8") as file:
                        file.write("自动")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                with open("gx.txt", "w", encoding="UTF-8") as file:
                    file.write("自动")
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                ts.mainloop()
            bc()
        def sd():
            def bc():
                lj = os.getcwd()
                try:
                    os.mkdir(lj + "\\设置")
                    with open("设置\\gx.txt", "w", encoding="UTF-8") as file:
                        file.write("手动")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
                except:
                    with open("设置\\gx.txt", "w", encoding="UTF-8") as file:
                        file.write("手动")
                    ts = Toplevel()
                    ts.title("提示")
                    Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                    t.Button(ts, text="重启程序", command=cq,bootstyle=sjanys()).pack()
                    ts.mainloop()
            bc()
        t.Radiobutton(zdgx, text="启动时自动检测更新", command=zd,bootstyle=sjys()).pack()
        t.Radiobutton(zdgx, text="启动手动检测更新", command=sd,bootstyle=sjys()).pack()
        zdgx.mainloop()
    def qrspyjsq():
        win = Toplevel()
        win.title("配置解释器")
        win.geometry("300x300")
        Label(win,text="配置嵌入式Python解释器",font=("kaiti",19)).pack()
        Label(win,text="嵌入式Python解释器配置简单，无需安装，使用方便").pack()
        Label(win, text="第一步，下载解释器并解压",font=("kaiti",15)).pack()
        def xzwj():
            dkwy("https://www.python.org/ftp/python/3.5.3/python-3.5.3-embed-win32.zip")
        t.Button(win,text="点此下载",bootstyle=sjanys(),command=xzwj).pack()
        Label(win, text="第二步，选择文件中python.exe文件路径", font=("kaiti",12)).pack()
        def getPath():
            import tkinter.filedialog
            # 选择文件path_接收文件地址
            path = tkinter.filedialog.askopenfilename()
            lj = os.getcwd()
            try:
                os.mkdir(lj + "\\设置")
                with open("设置\\jsqpath.txt", "w", encoding="UTF-8") as file:
                    file.write(path)
            except:
                with open("设置\\jsqpath.txt", "w", encoding="UTF-8") as file:
                    file.write(path)
        t.Button(win,text="配置路径",bootstyle=sjanys(),command=getPath).pack()
        Label(win, text="第三步，启用或禁止嵌入式解释器", font=("kaiti", 12)).pack()
        def qyjsq():
            lj = os.getcwd()
            try:
                os.mkdir(lj + "\\设置")
                with open("设置\\jsq.txt", "w", encoding="UTF-8") as file:
                    file.write("T")
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq, bootstyle=sjanys()).pack()
                ts.mainloop()
            except:
                with open("设置\\jsq.txt", "w", encoding="UTF-8") as file:
                    file.write("T")
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq, bootstyle=sjanys()).pack()
                ts.mainloop()
        def jyjsq():
            lj = os.getcwd()
            try:
                os.mkdir(lj + "\\设置")
                with open("设置\\jsq.txt", "w", encoding="UTF-8") as file:
                    file.write("F")
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq, bootstyle=sjanys()).pack()
                ts.mainloop()
            except:
                with open("设置\\jsq.txt", "w", encoding="UTF-8") as file:
                    file.write("F")
                ts = Toplevel()
                ts.title("提示")
                Label(ts, text="需要重启程序", font=("kaiti", 20)).pack()
                t.Button(ts, text="重启程序", command=cq, bootstyle=sjanys()).pack()
                ts.mainloop()
        t.Button(win, text="启用嵌入式解释器", bootstyle=sjanys(), command=qyjsq).pack()
        t.Button(win, text="禁用嵌入式解释器", bootstyle=sjanys(), command=jyjsq).pack()
        win.mainloop()
    t.Button(szdy,text="更改代码字体",command=ggzt,bootstyle=sjanys()).pack()
    t.Button(szdy, text="配置嵌入式Python解释器", command=qrspyjsq, bootstyle=sjanys()).pack()
    #t.Button(szdy, text="更改代码颜色", command=dmzt,bootstyle=sjanys()).pack()
    t.Button(szdy, text="更新设置", command=zdgx,bootstyle=sjanys()).pack()
    t.Button(szdy,text="自动保存设置",command=zdbcsz,bootstyle=sjanys()).pack()
    t.Button(szdy, text="关于", command=gy,bootstyle=sjanys()).pack()
    szdy.mainloop()

#翻译
def fy():
    import requests
    import sys
    import json
    import time

    def getCookies():
        cookies = ""
        if len(sys.argv) > 1:
            try:
                cookies = json.loads(sys.argv[1])["cookies"]
            except:
                pass
        return cookies

    def jsonLoads(str):
        try:
            return json.loads(str)
        except:
            return None

    # Information Transfer Protocol
    # Information exchange Protocol
    # 信息交换输出工具函数
    def InfoTransferAndExchange(data):
        time.sleep(0.01)
        jsonStr = json.dumps(data)
        print("#xzeysx#" + jsonStr + "#xzeysx#")

    '''
        // 提示信息
        data = { 'type':'msg','value': "识别前图片："+img_src }
        XesUtils.InfoTransferAndExchange(data)

        // 结果信息
        data = { 'type':'result','desc':'识别后图片','value' : imgurl }
        XesUtils.InfoTransferAndExchange(data)
    '''

    # 翻译
    def fy(text):
        text = text.strip()
        if text == "":
            return ""

        # print("语言服务正在处理中，请耐心等待...")

        params = {"text": text}
        cookies = getCookies()
        headers = {"Cookie": cookies}
        rep = requests.get("https://code.xueersi.com/api/ai/python_tts/translate", params=params, headers=headers)
        repDic = jsonLoads(rep.text)
        if repDic is None:
            raise Exception("微软语言服务请求超时，请稍后再试")

        if repDic["stat"] != 1:
            raise Exception(repDic["msg"])

        # print("语言服务处理完毕！")

        result = repDic["data"]["text"]
        xs = Toplevel()
        xs.title("翻译结果")
        from tkinter import Text
        T = Text(xs, font=zt, fg=fg, height=15, width=35)
        T.pack(fill=BOTH, expand=1)
        T.insert(END, result)
        # Label(xs,text=result,font=("微软雅黑",12),fg=fg).pack()
        xs.mainloop()

    # return result

    win = Toplevel()
    win.title("翻译")
    Label(win, text="翻译", font=("kaiti", 20)).pack()
    Label(win, text="请输入翻译内容", font="kaiti").pack()
    from tkinter import Text
    Text = Text(win, font=zt, fg=fg, height=15, width=35)
    Text.pack(fill=BOTH, expand=1)
    t.Button(win, text="翻译", command=lambda: fy(Text.get("1.0", END)),bootstyle=sjanys()).pack()

    win.mainloop()

#图片转文字
def tpzwz():
    import requests
    import base64

    def ocr(img_path: str) -> list:
        '''
        根据图片路径，将图片转为文字，返回识别到的字符串列表

        '''
        # 请求头
        headers = {
            'Host': 'cloud.baidu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.76',
            'Accept': '*/*',
            'Origin': 'https://cloud.baidu.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://cloud.baidu.com/product/ocr/general',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        }
        # 打开图片并对其使用 base64 编码
        with open(img_path, 'rb') as f:
            img = base64.b64encode(f.read())
        data = {
            'image': 'data:image/jpeg;base64,' + str(img)[2:-1],
            'image_url': '',
            'type': 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic',
            'detect_direction': 'false'
        }
        # 开始调用 ocr 的 api
        response = requests.post(
            'https://cloud.baidu.com/aidemo', headers=headers, data=data)

        # 设置一个空的列表，后面用来存储识别到的字符串
        ocr_text = []
        result = response.json()['data']
        if not result.get('words_result'):
            return []

        # 将识别的字符串添加到列表里面
        for r in result['words_result']:
            text = r['words'].strip()
            ocr_text.append(text)
        # 返回字符串列表
        return ocr_text

    win = Toplevel()
    win.title('图片转文字')
    win.geometry("300x160")
    Label(win, text='图片转文字', font=("kaiti", 20)).pack()
    Label(win, text='请输入图片名称', font=("kaiti", 20)).pack()
    mc = Entry(win)
    mc.pack()

    def zs():
        img_path = mc.get()
        # content 是识别后得到的结果
        content = "".join(ocr(img_path))
        # 输出结果
        zs = Toplevel()
        zs.title('图片转文字结果')
        T = Text(zs, height=10, width=50)
        T.insert(END, content)
        T.pack(fill=BOTH, expand=YES)
        zs.mainloop()
    def xzpath():
        from tkinter import filedialog
        img_path = filedialog.askopenfilename()
        content = "".join(ocr(img_path))
        # 输出结果
        zs = Toplevel()
        zs.title('图片转文字结果')
        T = Text(zs, height=10, width=50)
        T.insert(END, content)
        T.pack(fill=BOTH, expand=YES)
        zs.mainloop()
    t.Button(win, text='转换', command=zs,bootstyle=sjanys()).pack()
    t.Button(win, text='选取路径', command=xzpath, bootstyle=sjanys()).pack()
    win.mainloop()

#音乐下载站
def yyxzz():
    import requests
    import bs4
    import lxml
    xzyy = Toplevel()
    xzyy.title('音乐下载站')
    xzyy.geometry('250x140')
    Label(xzyy, text='请输入音乐名称:').pack()
    hqmc = t.Entry(xzyy,bootstyle=sjys())
    hqmc.pack()
    def pqyy():
        import threading
        xzyy = threading.Thread(target=pqyyjb)
        xzyy.start()
    def pqyyjb():
        try:
            mc = hqmc.get()
            #作答区域2：拼接音乐链接的后半部分n.a["href"]
            music_url = "https://algfwq.github.io/YYXZZ/" + mc
            # 保存音乐二进制数据
            res = requests.get(music_url)
            music = res.content
            file_name = mc
            with open(file_name, "wb") as file:
                file.write(music)
        except:
            jgjg = Toplevel()
            jgjg.title("警告！")
            Label(jgjg, text="音乐下载失败！可能是因为网站更新，或网络原因！可以联系QQ：3104374883！").pack()
            jgjg.mainloop()
    def yylb():
        try:
            pqsj = requests.get("https://algfwq.github.io/YYXZZ/")
            pqsj.encoding = "UTF-8"
            soup = bs4.BeautifulSoup(pqsj.text, "lxml")
            yylb = soup.find_all("a")
            lb = Toplevel()
            lb.title("音乐列表")
            a = Text(lb, width=50, height=20)
            a.pack()
            for i in yylb:
                a.insert(END, i.text+"\n")
            lb.mainloop()
        except:
            jgjg = Toplevel()
            jgjg.title("警告！")
            Label(jgjg, text="音乐下载失败！可能是因为网站更新，或网络原因！可以联系QQ：3104374883！").pack()
            jgjg.mainloop()
    t.Button(xzyy, text='查看音乐列表', command=yylb,bootstyle=sjanys()).pack()
    t.Button(xzyy, text='确定', command=pqyy,bootstyle=sjanys()).pack()
    xzyy.mainloop()



#插件核心
def cjan(cj,mc,nr,hs):
    Label(cj, text=mc, font=("kaiti",15)).pack()
    t.Button(cj, text="运行", command=hs,bootstyle=sjanys()).pack()
    def xq():
        xq = Toplevel()
        xq.title(mc)
        Label(xq, text=mc, font=("kaiti",20)).pack()
        Label(xq, text=nr, font=("kaiti",15)).pack()
        xq.mainloop()
    t.Button(cj, text="插件详情", command=xq,bootstyle=sjanys()).pack()



#插件简介
fyjj = '''奥利给官方研发的翻译插件'''
tpzwzjj = '''奥利给官方制作的图片转文字工具
可以帮助您提取图片文字
和QQ提取文字差不多
但效果更好'''
yyxzzjj='''奥利给官方制作的免费音乐下载站
你可以在这里免费下载任何音乐
现在音乐不怎么多
如果你想加入一些音乐
请联系QQ：3104374883
'''
#-------

def cj():
    win = Toplevel()
    canvas = Canvas(win, width=200, height=310000, scrollregion=(0, 0, 820, 2050))  # 创建canvas
    cj = Frame(canvas, height=100)  # 用框架换掉窗口，方便滚动
    win.title("插件")
    win.geometry("300x300")
    # sb = Scrollbar(dmts)
    # sb.pack(side=RIGHT, fill=Y)
    # 这个scrollbar没有用了，看下面那个

    # 标准节
    # Label(dmts, text="print()，输出").pack()
    # def dm():
    #     fz("print()")
    # Button(dmts, text="复制代码", command=dm).pack()
    # 已上为标准节
    for i in range(0):
        Label(cj, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()
    # Label(dmts, text="  ").pack()

    cjan(cj,"翻译",fyjj,fy)
    cjan(cj,"图片转文字",tpzwzjj,tpzwz)
    cjan(cj,"音乐下载站",yyxzzjj,yyxzz)

    for i in range(9):
        Label(cj, text="  ").pack()

    vbar = t.Scrollbar(win, orient=VERTICAL, command=canvas.yview,bootstyle=sjgdtys())  # 竖直滚动条
    # vbar.place(x=280, y=0, height=300)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.config(yscrollcommand=vbar.set)
    cj.pack()  # 显示控件
    canvas.pack()
    canvas.create_window((90, 240), window=cj)  # create_window,让他们互相绑定
    win.mainloop()
#随机滚动条样式
def sjgdtys():
    import random
    ys = random.randint(1,7)
    if ys == 1:
        ysm = "default"
    if ys == 2:
        ysm = "primary"
    if ys == 3:
        ysm = "success"
    if ys == 4:
        ysm = "info"
    if ys == 5:
        ysm = "warning"
    if ys == 6:
        ysm = "danger"
    if ys == 7:
        ysm = "dark"

    fh = ysm + "-round"
    return fh
#随机样式
def sjys():
    import random
    ys = random.randint(1, 7)
    if ys == 1:
        ysm = "default"
    if ys == 2:
        ysm = "primary"
    if ys == 3:
        ysm = "success"
    if ys == 4:
        ysm = "info"
    if ys == 5:
        ysm = "warning"
    if ys == 6:
        ysm = "danger"
    if ys == 7:
        ysm = "dark"

    return ysm
#随机按钮颜色
def sjanys():
    import random
    ys = random.randint(1,7)
    if ys == 1:
        ysm = "default"
    if ys == 2:
        ysm = "primary"
    if ys == 3:
        ysm = "success"
    if ys == 4:
        ysm = "info"
    if ys == 5:
        ysm = "warning"
    if ys == 6:
        ysm = "danger"
    if ys == 7:
        ysm = "dark"

    fh = ysm + "-outline"
    return fh
#主窗口
#zck = t.Tk()
zck = t.Window(themename="cosmo")
zck.title("奥利给开发者编译器3.0")
zck.geometry("300x385")
zck.call('tk', 'scaling', ScaleFactor/75)


#自动更新检查
try:
    with open("设置\\gx.txt","r",encoding="UTF-8")as file:
        zdgx = file.read()
except:
    zdgx = "手动"


#字体设置
try:
    with open("设置\\zt.txt","r",encoding="UTF-8")as file:
        dqzt = file.read()
        zt = dqzt
except:
    zt = "Consolas"
#zt = "Consolas"

#代码字体颜色
try:
    with open("设置\\fg.txt","r",encoding="UTF-8")as file:
        dqfg = file.read()
        fg = dqfg
except:
    fg = "Black"

#fg = "Black"
#fg = "green"
#fg = "Lime"
i2 = '''#以下是示例代码
print("欢迎使用奥利给Python编译器！！！")
'''
#示例代码
try:
    with open("设置\\sldm.txt","r",encoding="UTF-8")as file:
        dqdm = file.read()
        i = dqdm
except:
    i = i2

try:
    with open("设置\\htmlsldm.txt","r",encoding="UTF-8")as file:
        dqdm = file.read()
        ihtmldm = dqdm
except:
    ihtmldm = ihtml

#字体颜色
try:
    with open("设置\\ztys.txt","r",encoding="UTF-8")as file:
        dqztys = file.read()
        ztys = dqztys
except:
    ztys = "Black"

#ztys="Black"

Label(zck, text="奥利给开发者编译器", font=("kaiti",20)).pack()
Label(zck, text="一个专业轻巧的编译器").pack()
Label(zck, text="制作团队：奥利给硬件科技工作室").pack()
#Label(zck,text="请确保此电脑已安装Python",fg=ztys).pack()
Label(zck, text="请以管理员身份运行此程序").pack()
a = Label(zck, text="点击前往官网")
a.pack()
def open_url(event):
    dkwy("https://site-5888287-8893-396.mystrikingly.com/")
a.bind("<Button-1>", open_url)
t.Button(zck,text="新建文件",command=xjwj,bootstyle=sjanys()).pack()
t.Button(zck,text="读取文件",command=dqwj,bootstyle=sjanys()).pack()
t.Button(zck,text="库管理",command=kgl,bootstyle=sjanys()).pack()
t.Button(zck,text="背景音乐",command=yy,bootstyle=sjanys()).pack()
#Button(zck,text="代码提示",command=dmts,font=("kaiti",15),fg=ztys).pack()
t.Button(zck,text="更多插件",command=cj,bootstyle=sjanys()).pack()
t.Button(zck,text="检查更新",command=gxbb,bootstyle=sjanys()).pack()
t.Button(zck,text="设置",command=gxsz,bootstyle=sjanys()).pack()
if zdgx == "自动":
    gxbb()
zck.mainloop()
