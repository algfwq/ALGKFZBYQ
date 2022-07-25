"""Complete either attribute names or file names.

Either on demand or after a user-selected delay after a key character,
pop up a list of candidates.
"""
"""完成属性名或文件名。 根据需要或者在一个关键字符之后用户选择的延迟之后，弹出候选人名单。 """

import __main__
import keyword
import os
import string
import sys

# Modified keyword list is used in fetch_completions.
# fetch _ completions中使用了修改的关键字列表。

completion_kwds = [s for s in keyword.kwlist
                     if s not in {'True', 'False', 'None'}]  # In builtins.,#内置。
completion_kwds.extend(('match', 'case'))  # Context keywords.,#上下文关键字。
completion_kwds.sort()

# Two types of completions; defined here for autocomplete_w import below.
#两种类型的完井；此处定义用于下面的autocomplete_w导入。

ATTRS, FILES = 0, 1
from idlelib import autocomplete_w
from idlelib.config import idleConf
from idlelib.hyperparser import HyperParser

# Tuples passed to open_completions.
#       EvalFunc, Complete, WantWin, Mode
#传递给open_completions的元组数。
# EvalFunc，Complete，WantWin，Mode

FORCE = True,     False,    True,    None   # Control-Space.,控制空间。
TAB   = False,    True,     True,    None   # Tab.,标签。
TRY_A = False,    False,    False,   ATTRS  # '.' for attributes.,'.'对于属性。
TRY_F = False,    False,    False,   FILES  # '/' in quotes for file name.,文件名用引号括起来。

# This string includes all chars that may be in an identifier.
# TODO Update this here and elsewhere.
#该字符串包括可能在标识符中的所有字符。
# TODO在此处和其他地方更新此内容。

ID_CHARS = string.ascii_letters + string.digits + "_"

SEPS = f"{os.sep}{os.altsep if os.altsep else ''}"
TRIGGERS = f".{SEPS}"

class AutoComplete:

    def __init__(self, editwin=None, tags=None):
        self.editwin = editwin
        if editwin is not None:   # not in subprocess or no-gui test,#不在子流程或无gui测试中
            self.text = editwin.text
        self.tags = tags
        self.autocompletewindow = None
        # id of delayed call, and the index of the text insert when
        # the delayed call was issued. If _delayed_completion_id is
        # None, there is no delayed call.
        # 延迟呼叫的id，以及插入时文本的索引
        # #延迟的呼叫已发出。如果延迟完成标识为
        # #无，没有延迟呼叫。

        self._delayed_completion_id = None
        self._delayed_completion_index = None

    @classmethod
    def reload(cls):
        cls.popupwait = idleConf.GetOption(
            "extensions", "AutoComplete", "popupwait", type="int", default=0)

    def _make_autocomplete_window(self):  # Makes mocking easier.,#让嘲笑变得更容易。
        return autocomplete_w.AutoCompleteWindow(self.text, tags=self.tags)

    def _remove_autocomplete_window(self, event=None):
        if self.autocompletewindow:
            self.autocompletewindow.hide_window()
            self.autocompletewindow = None

    def force_open_completions_event(self, event):
        "(^space) Open completion list, even if a function call is needed."
        "(^space)打开完成列表，即使需要函数调用."
        self.open_completions(FORCE)
        return "break"

    def autocomplete_event(self, event):
        "(tab) Complete word or open list if multiple options."
        "(tab)如果有多个选项，请完成word或打开列表。"

        if hasattr(event, "mc_state") and event.mc_state or\
                not self.text.get("insert linestart", "insert").strip():
            # A modifier was pressed along with the tab or
            # there is only previous whitespace on this line, so tab.
            # 一个修饰键和标签一起被按下，或者
            # #这一行只有前面的空格，所以用tab键。

            return None
        if self.autocompletewindow and self.autocompletewindow.is_active():
            self.autocompletewindow.complete()
            return "break"
        else:
            opened = self.open_completions(TAB)
            return "break" if opened else None

    def try_open_completions_event(self, event=None):
        "(./) Open completion list after pause with no movement."
        "(./)暂停无动作后打开完成列表。"

        lastchar = self.text.get("insert-1c")
        if lastchar in TRIGGERS:
            args = TRY_A if lastchar == "." else TRY_F
            self._delayed_completion_index = self.text.index("insert")
            if self._delayed_completion_id is not None:
                self.text.after_cancel(self._delayed_completion_id)
            self._delayed_completion_id = self.text.after(
                self.popupwait, self._delayed_open_completions, args)

    def _delayed_open_completions(self, args):
        "Call open_completions if index unchanged."
        "如果索引不变，调用open_completions . "

        self._delayed_completion_id = None
        if self.text.index("insert") == self._delayed_completion_index:
            self.open_completions(args)

    def open_completions(self, args):
        """Find the completions and create the AutoCompleteWindow.
        Return True if successful (no syntax error or so found).
        If complete is True, then if there's nothing to complete and no
        start of completion, won't open completions and return False.
        If mode is given, will open a completion list only in this mode.
        """
        '''
        查找完成并创建自动完成窗口。如果成功，则返回True(没有发现语法错误)。
        如果完成是真的，那么如果没有什么要完成，没有开始完成，不会打开完成并返回False。
        如果给定了模式，将仅在此模式下打开完成列表。
        '''

        evalfuncs, complete, wantwin, mode = args
        # Cancel another delayed call, if it exists.
        # 取消另一个延迟的呼叫(如果存在)。

        if self._delayed_completion_id is not None:
            self.text.after_cancel(self._delayed_completion_id)
            self._delayed_completion_id = None

        hp = HyperParser(self.editwin, "insert")
        curline = self.text.get("insert linestart", "insert")
        i = j = len(curline)
        if hp.is_in_string() and (not mode or mode==FILES):
            # Find the beginning of the string.
            # fetch_completions will look at the file system to determine
            # whether the string value constitutes an actual file name
            # XXX could consider raw strings here and unescape the string
            # value if it's not raw.
            # 找到字符串的开头。
            # fetch_completions将查看文件系统以确定
            # #字符串值是否构成实际的文件名
            # XXX可以在这里考虑原始字符串并取消对该字符串的转义 #如果不是原始值。

            self._remove_autocomplete_window()
            mode = FILES
            # Find last separator or string start
            # 查找最后一个分隔符或字符串开头

            while i and curline[i-1] not in "'\"" + SEPS:
                i -= 1
            comp_start = curline[i:j]
            j = i
            # Find string start
            # 查找字符串开头

            while i and curline[i-1] not in "'\"":
                i -= 1
            comp_what = curline[i:j]
        elif hp.is_in_code() and (not mode or mode==ATTRS):
            self._remove_autocomplete_window()
            mode = ATTRS
            while i and (curline[i-1] in ID_CHARS or ord(curline[i-1]) > 127):
                i -= 1
            comp_start = curline[i:j]
            if i and curline[i-1] == '.':  # Need object with attributes.,#需要具有属性的对象。
                hp.set_index("insert-%dc" % (len(curline)-(i-1)))
                comp_what = hp.get_expression()
                if (not comp_what or
                   (not evalfuncs and comp_what.find('(') != -1)):
                    return None
            else:
                comp_what = ""
        else:
            return None

        if complete and not comp_what and not comp_start:
            return None
        comp_lists = self.fetch_completions(comp_what, mode)
        if not comp_lists[0]:
            return None
        self.autocompletewindow = self._make_autocomplete_window()
        return not self.autocompletewindow.show_window(
                comp_lists, "insert-%dc" % len(comp_start),
                complete, mode, wantwin)

    def fetch_completions(self, what, mode):
        """Return a pair of lists of completions for something. The first list
        is a sublist of the second. Both are sorted.

        If there is a Python subprocess, get the comp. list there.  Otherwise,
        either fetch_completions() is running in the subprocess itself or it
        was called in an IDLE EditorWindow before any script had been run.

        The subprocess environment is that of the most recently run script.  If
        two unrelated modules are being edited some calltips in the current
        module may be inoperative if the module was not the last to run.
        """
        "返回某物的一对完成列表。第一份名单是第二个。"
        "两个都排序了。 如果有Python子流程，则获取comp。"
        "列在那里。否则， fetch_completions()正在子流程本身或其中运行在运行任何脚本之前，"
        "在空闲的EditorWindow中调用了。 "
        "子进程环境是最近运行的脚本的环境。"
        "如果两个不相关的模块正在被编辑如果模块不是最后运行的，模块可能不工作。 "

        try:
            rpcclt = self.editwin.flist.pyshell.interp.rpcclt
        except:
            rpcclt = None
        if rpcclt:
            return rpcclt.remotecall("exec", "get_the_completion_list",
                                     (what, mode), {})
        else:
            if mode == ATTRS:
                if what == "":  # Main module names.
                    namespace = {**__main__.__builtins__.__dict__,
                                 **__main__.__dict__}
                    bigl = eval("dir()", namespace)
                    bigl.extend(completion_kwds)
                    bigl.sort()
                    if "__all__" in bigl:
                        smalll = sorted(eval("__all__", namespace))
                    else:
                        smalll = [s for s in bigl if s[:1] != '_']
                else:
                    try:
                        entity = self.get_entity(what)
                        bigl = dir(entity)
                        bigl.sort()
                        if "__all__" in bigl:
                            smalll = sorted(entity.__all__)
                        else:
                            smalll = [s for s in bigl if s[:1] != '_']
                    except:
                        return [], []

            elif mode == FILES:
                if what == "":
                    what = "."
                try:
                    expandedpath = os.path.expanduser(what)
                    bigl = os.listdir(expandedpath)
                    bigl.sort()
                    smalll = [s for s in bigl if s[:1] != '.']
                except OSError:
                    return [], []

            if not smalll:
                smalll = bigl
            return smalll, bigl

    def get_entity(self, name):
        "Lookup name in a namespace spanning sys.modules and __main.dict__."
        "在跨越sys.modules和__main.dict__的命名空间中查找名称。"
        return eval(name, {**sys.modules, **__main__.__dict__})


AutoComplete.reload()

if __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_autocomplete', verbosity=2)
