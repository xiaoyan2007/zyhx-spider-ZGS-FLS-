import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# ===================== 自动获取图标路径 =====================
def get_icon_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "logo.ico")
    return "logo.ico"

# ===================== 爬虫配置：随机UA防拦截 =====================
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]
EXCLUDE_TEXT = ["《 人民日报 》", "分享让更多人看到", "人民日报", "登录人民网", "版权所有"]
session = requests.Session()

def log(text_widget, msg):
    text_widget.insert(tk.END, msg + "\n")
    text_widget.see(tk.END)
    text_widget.update()

def get_article_content(url):
    headers = {"User-Agent": random.choice(UA_LIST), "Referer":"https://data.people.com.cn/"}
    try:
        res = session.get(url, headers=headers, timeout=15)
        try:
            res.content.decode("gbk")
            res.encoding = "gbk"
        except:
            res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        p_list = soup.find_all("p")
        raw_txt = "\n".join([p.get_text() for p in p_list])
        for ban_str in EXCLUDE_TEXT:
            raw_txt = raw_txt.replace(ban_str, "")
        return raw_txt
    except Exception as e:
        return ""

def get_outline_list(keyword, sdate, edate, maxpage, log_box):
    page = 1
    art_list = []
    base_qs = {
        "cds": [
            {"fld": "dataTime.start", "cdr": "AND", "val": sdate},
            {"fld": "dataTime.end", "cdr": "AND", "val": edate},
            {"cdr": "AND", "cds": [
                {"fld": "title", "OR": "OR", "val": keyword},
                {"fld": "subTitle", "OR": "OR", "val": keyword}
            ]}
        ],
        "obs": [{"fld": "dataTime.desc", "cdr": "DESC"}],
        "tr": "A", "ss": "1", "pageNo": 1, "pageSize": 20
    }
    while page <= maxpage:
        log(log_box, f"正在抓取第 {page} 页目录...")
        base_qs["pageNo"] = page
        qs_str = urllib.parse.quote(json.dumps(base_qs))
        url = f"https://data.people.com.cn/rmrb/s?qs={qs_str}"
        headers = {"User-Agent": random.choice(UA_LIST), "Referer":"https://data.people.com.cn/rmrb/"}
        try:
            resp = session.get(url, headers=headers, timeout=12)
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("div.sreach_li")
            if not items:
                log(log_box, "无更多数据，结束目录抓取")
                break
            for item in items:
                title_tag = item.select_one("a.open_detail_link")
                h3_a = item.select_one("h3 a")
                date_tag = item.select_one("div.listinfo")
                kw_tags = item.select('a[href*="/rmrb/s"]')
                if not all([title_tag, h3_a, date_tag]):
                    continue
                title = title_tag.get_text(strip=True)
                link = "https://data.people.com.cn" + h3_a["href"]
                date = date_tag.get_text(strip=True)
                kw = ",".join([k.get_text(strip=True) for k in kw_tags])
                art_list.append([title, link, date, kw])
                log(log_box, f"已抓取文章：{title}")
                time.sleep(random.uniform(0.3,0.8))
            page += 1
            time.sleep(random.uniform(2,4))
        except Exception as err:
            log(log_box, f"目录抓取异常：{str(err)}")
            break
    return art_list

def start_crawl(key, start, end, pages, clean_enabled, log_box):
    try:
        pages = int(pages)
    except:
        messagebox.showerror("错误", "页数必须是数字")
        return
    if not key or not start or not end:
        messagebox.showwarning("提示", "请填写完整")
        return

    log(log_box, "="*50)
    log(log_box, "开始爬取...")
    article_data = get_outline_list(key, start, end, pages, log_box)
    log(log_box, f"共获取到 {len(article_data)} 篇文章")

    all_content = ""
    for idx, (title, url, d, kw) in enumerate(article_data):
        log(log_box, f"正在抓取正文 {idx+1}/{len(article_data)}")
        cont = get_article_content(url)

        if clean_enabled:
            cont = ''.join(cont.split())
            all_content += cont
        else:
            all_content += f"【文章{idx+1}】\n{cont}\n\n"

        time.sleep(random.uniform(1.5,3.5))

    with open("outline.txt", "w", encoding="utf-8") as f:
        for t, l, d, k in article_data:
            f.write(f"标题：{t}\n链接：{l}\n日期：{d}\n关键词：{k}\n\n")

    with open("contents.txt", "w", encoding="utf-8") as f:
        f.write(all_content.strip())

    log(log_box, "✅ 全部完成！已保存 outline.txt 和 contents.txt")
    messagebox.showinfo("完成", "爬取完毕！")

# ===================== 免责声明弹窗 =====================
def show_legal_disclaimer():
    root = tk.Tk()
    root.withdraw()

    disclaimer_text = """
    智宇慧轩爬虫 —— 法律免责与合规使用声明

    1. 工具性质
    本软件仅为网页解析、文本提取的技术学习工具，不提供任何破解、绕过权限、批量非法爬取功能。

    2. 合法使用范围
    仅限在浙江工商大学图书馆授权范围内、个人学习与科研目的使用；
    严禁商用、倒卖数据、批量非法抓取、传播受版权保护内容。

    3. 法律依据
    使用者必须遵守：
    ✔《中华人民共和国著作权法》
    ✔《中华人民共和国网络安全法》
    ✔《中华人民共和国数据安全法》
    ✔《中华人民共和国个人信息保护法》
    ✔ 目标网站 robots 协议与用户协议

    4. 责任划分
    一切违规使用行为产生的法律责任、民事赔偿、行政或刑事责任，
    均由使用者自行承担，开发者不承担任何连带责任。

    5. 风险提示
    程序可能因目标网站改版导致解析异常，使用者需自行核验数据有效性。
    """

    def on_agree():
        if agree_var.get():
            win.destroy()
            run_gui()
        else:
            messagebox.showwarning("提示", "请勾选同意免责声明")

    win = tk.Toplevel()
    win.title("免责与合规声明")
    win.geometry("650x430")
    win.protocol("WM_DELETE_WINDOW", lambda: exit())

    try:
        win.iconbitmap(get_icon_path())
    except:
        pass

    tk.Label(win, text="⚠️  法律免责声明", font=("微软雅黑", 14, "bold"), fg="red").pack(pady=8)
    text_box = tk.Text(win, width=80, height=18)
    text_box.pack(padx=15)
    text_box.insert(tk.END, disclaimer_text)
    text_box.config(state=tk.DISABLED)

    agree_var = tk.BooleanVar()
    tk.Checkbutton(win, text="我已阅读并同意以上全部条款，仅在合法授权范围内合规使用", variable=agree_var).pack(pady=5)

    tk.Button(win, text="确认并进入程序", bg="#28a745", fg="white", width=22, command=on_agree).pack(pady=6)
    win.mainloop()

# ===================== GUI界面 =====================
import webbrowser

def open_link(event):
    webbrowser.open("https://lib.zjgsu.edu.cn/1020/list.htm")

def run_gui():
    window = tk.Tk()
    window.title("智宇慧轩爬虫 Beta 0.2")

    try:
        window.iconbitmap(get_icon_path())
    except:
        pass

    window.geometry("900x480")

    tip_frame = tk.Frame(window)
    tip_frame.pack(pady=12, padx=20, fill="x")
    lab1 = tk.Label(tip_frame, text="欢迎使用智宇慧轩爬虫 Beta 0.2",font=("宋体", 11, "bold"), fg="black", justify="center")
    lab1.pack(anchor="center")
    lab2 = tk.Label(tip_frame, text="本爬虫可依据用户选定的关键词与时间范围，自动抓取人民日报数据库相关文章正文；正文经数据清洗后存储至content.txt，文章基础信息汇总整理至outline.txt。",wraplength=860, justify="left")
    lab2.pack(anchor="w", pady=2)
    lab3 = tk.Label(tip_frame, text="“爬取页数”参数指定的是搜索每天报纸的前x页范围的文章，数字越小，爬取越快，内容也越少",wraplength=860, justify="left")
    lab3.pack(anchor="w", pady=2)
    lab4 = tk.Label(tip_frame, text="注意：程序可能因目标网站改版导致解析异常，使用者需自行在content.txt核验数据有效性。",wraplength=860, fg="red", justify="left")
    lab4.pack(anchor="w", pady=2)

    lab5 = tk.Label(
        tip_frame,
        text="使用本爬虫前请从浙江工商大学图书馆官网（https://lib.zjgsu.edu.cn/1020/list.htm）进入人民日报数据库，否则无法爬取信息，点击本行文字可直接跳转",
        wraplength=850, fg="blue", cursor="hand2", justify="left"
    )
    lab5.pack(anchor="w", pady=2)
    lab5.bind("<Button-1>", open_link)

    lab6 = tk.Label(tip_frame, text="严禁使用本程序从事任何非法活动。",font=("宋体", 9, "bold"), fg="red", justify="left")
    lab6.pack(anchor="w", pady=2)

    frame = tk.Frame(window)
    frame.pack(pady=10)
    input_frame = tk.Frame(frame)
    input_frame.grid(row=0, column=0, padx=20)

    tk.Label(input_frame, text="关键词：").grid(row=0, column=0, sticky="e", pady=8)
    key_entry = ttk.Entry(input_frame, width=28)
    key_entry.grid(row=0, column=1)

    tk.Label(input_frame, text="开始日期：").grid(row=1, column=0, sticky="e", pady=8)
    start_entry = ttk.Entry(input_frame, width=28)
    start_entry.grid(row=1, column=1)
    start_entry.insert(0, "2025-01-01")

    tk.Label(input_frame, text="结束日期：").grid(row=2, column=0, sticky="e", pady=8)
    end_entry = ttk.Entry(input_frame, width=28)
    end_entry.grid(row=2, column=1)
    end_entry.insert(0, "2025-12-31")

    tk.Label(input_frame, text="爬取页数：").grid(row=3, column=0, sticky="e", pady=8)
    page_entry = ttk.Entry(input_frame, width=28)
    page_entry.grid(row=3, column=1)
    page_entry.insert(0, "2")

    clean_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        input_frame, text="语料清洗（去空格/换行/合成一段）",
        variable=clean_var
    ).grid(row=4, column=1, sticky="w", pady=4)

    def run():
        k = key_entry.get().strip()
        s = start_entry.get().strip()
        e = end_entry.get().strip()
        p = page_entry.get().strip()
        clean_on = clean_var.get()
        start_crawl(k, s, e, p, clean_on, log_box)

    ttk.Button(input_frame, text="开始爬取", command=run).grid(row=5, column=1, pady=15)

    log_frame = tk.Frame(frame)
    log_frame.grid(row=0, column=1, padx=10)
    tk.Label(log_frame, text="运行日志").pack()
    log_box = tk.Text(log_frame, width=42, height=18)
    log_box.pack()
    log(log_box, "日志已启动，等待操作...")

    window.mainloop()

if __name__ == "__main__":
    show_legal_disclaimer()
