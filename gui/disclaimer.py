"""
免责声明弹窗模块
"""

import tkinter as tk
from tkinter import messagebox
import webbrowser

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    get_icon_path,
    DISCLAIMER_TITLE,
    DISCLAIMER_SIZE,
    DISCLAIMER_TEXT
)


def show_disclaimer_window(on_agree_callback):
    """
    显示免责声明弹窗
    
    Args:
        on_agree_callback: 用户同意后的回调函数
    """
    root = tk.Tk()
    root.withdraw()
    
    def on_agree():
        if agree_var.get():
            win.destroy()
            on_agree_callback()
        else:
            messagebox.showwarning("提示", "请勾选同意免责声明")
    
    win = tk.Toplevel()
    win.title(DISCLAIMER_TITLE)
    win.geometry(DISCLAIMER_SIZE)
    win.protocol("WM_DELETE_WINDOW", lambda: exit())
    
    # 设置图标
    try:
        win.iconbitmap(get_icon_path())
    except:
        pass
    
    # 标题
    tk.Label(
        win,
        text="⚠️  法律免责声明",
        font=("微软雅黑", 14, "bold"),
        fg="red"
    ).pack(pady=8)
    
    # 声明文本框
    text_box = tk.Text(win, width=78, height=20)
    text_box.pack(padx=15)
    text_box.insert(tk.END, DISCLAIMER_TEXT)
    text_box.config(state=tk.DISABLED)
    
    # 同意复选框
    agree_var = tk.BooleanVar()
    tk.Checkbutton(
        win,
        text="我已阅读并同意以上全部条款，仅在合法授权范围内合规使用",
        variable=agree_var
    ).pack(pady=5)
    
    # 确认按钮
    tk.Button(
        win,
        text="确认并进入程序",
        bg="#28a745",
        fg="white",
        width=22,
        command=on_agree
    ).pack(pady=6)
    
    win.mainloop()
