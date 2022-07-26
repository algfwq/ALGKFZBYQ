import tkinter as tk


class mainUI():
    def insert_position(self, event):
        self.insert_position = self.text.index("insert")
        print(self.insert_position)
        self.win.title('text---ln:{} col:{}'.format(*str(self.insert_position).split('.')))

    def __init__(self):
        self.win = tk.Tk()
        self.win.title('text')
        self.win.geometry('500x500')
        self.scrollbar = tk.Scrollbar()
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(self.win, wrap="none", bg="white", fg="black", font=('微软雅黑', 10), insertbackground='blue')
        self.scrollbar.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.scrollbar.set)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.bind("<ButtonRelease-1>", self.insert_position)
        self.win.bind("<KeyRelease>", self.insert_position)
        # self.text.bind("<B1-Motion>",self.insert_position) 这个是当鼠标按下并移动时自动刷新光标位置


def main():
    mainrun = mainUI()
    mainrun.win.mainloop()


if __name__ == '__main__':
    main()