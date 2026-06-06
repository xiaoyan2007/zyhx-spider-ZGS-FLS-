"""
主界面模块
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import threading
import queue

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    get_icon_path,
    WINDOW_TITLE,
    WINDOW_SIZE,
    ZJGSU_LIBRARY_URL,
    OUTLINE_FILENAME,
    CONTENTS_FILENAME
)
from utils.logger import log
from utils.validators import validate_inputs
from crawler.core import Crawler
from gui.captcha_dialog import show_captcha_dialog


def open_zjgsu_link(event=None):
    """打开浙江工商大学图书馆链接"""
    webbrowser.open(ZJGSU_LIBRARY_URL)


def run_gui():
    """运行主界面"""
    window = tk.Tk()
    window.title(WINDOW_TITLE)
    window.geometry(WINDOW_SIZE)
    
    # 设置图标
    try:
        window.iconbitmap(get_icon_path())
    except:
        pass
    
    # ===================== 顶部说明区域 =====================
    tip_frame = tk.Frame(window)
    tip_frame.pack(pady=12, padx=20, fill="x")
    
    tk.Label(
        tip_frame,
        text="欢迎使用智宇慧轩爬虫 Beta 0.2",
        font=("宋体", 11, "bold"),
        fg="black",
        justify="center"
    ).pack(anchor="center")
    
    tk.Label(
        tip_frame,
        text="本爬虫可依据用户选定的关键词与时间范围，自动抓取人民日报数据库相关文章正文；"
             "正文经数据清洗后存储至 content.txt，文章基础信息汇总整理至 outline.txt。",
        wraplength=860,
        justify="left"
    ).pack(anchor="w", pady=2)
    
    tk.Label(
        tip_frame,
        text="爬取页数参数指定的是搜索每天报纸的前x页范围的文章，数字越小，爬取越快，内容也越少",
        wraplength=860,
        justify="left"
    ).pack(anchor="w", pady=2)
    
    tk.Label(
        tip_frame,
        text="注意：程序可能因目标网站改版导致解析异常，使用者需自行在 content.txt 核验数据有效性。",
        wraplength=860,
        justify="left"
    ).pack(anchor="w", pady=2)
    
    lab5 = tk.Label(
        tip_frame,
        text="使用本爬虫前请从浙江工商大学图书馆官网进入人民日报数据库，否则无法爬取信息，点击本行文字可直接跳转",
        wraplength=860,
        fg="blue",
        cursor="hand2",
        justify="left"
    )
    lab5.pack(anchor="w", pady=2)
    lab5.bind("<Button-1>", open_zjgsu_link)
    
    tk.Label(
        tip_frame,
        text="严禁使用本程序从事任何非法活动。",
        font=("宋体", 9, "bold"),
        fg="red",
        justify="left"
    ).pack(anchor="w", pady=2)
    
    # ===================== 输入区域 =====================
    frame = tk.Frame(window)
    frame.pack(pady=10)
    
    input_frame = tk.Frame(frame)
    input_frame.grid(row=0, column=0, padx=20)
    
    # 关键词
    tk.Label(input_frame, text="关键词：").grid(row=0, column=0, sticky="e", pady=8)
    key_entry = ttk.Entry(input_frame, width=28)
    key_entry.grid(row=0, column=1)
    key_entry.insert(0, "全国政协举行新年茶话会")
    
    # 开始日期
    tk.Label(input_frame, text="开始日期：").grid(row=1, column=0, sticky="e", pady=8)
    start_entry = ttk.Entry(input_frame, width=28)
    start_entry.grid(row=1, column=1)
    start_entry.insert(0, "2026-01-01")
    
    # 结束日期
    tk.Label(input_frame, text="结束日期：").grid(row=2, column=0, sticky="e", pady=8)
    end_entry = ttk.Entry(input_frame, width=28)
    end_entry.grid(row=2, column=1)
    end_entry.insert(0, "2026-01-01")
    
    # 爬取页数
    tk.Label(input_frame, text="爬取页数：").grid(row=3, column=0, sticky="e", pady=8)
    page_entry = ttk.Entry(input_frame, width=28)
    page_entry.grid(row=3, column=1)
    page_entry.insert(0, "1")
    
    # 语料清洗开关
    clean_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        input_frame,
        text="语料清洗（去空格/换行/合成一段）",
        variable=clean_var
    ).grid(row=4, column=1, sticky="w", pady=4)
    
    # 验证码处理方式
    tk.Label(input_frame, text="验证码处理：").grid(row=5, column=0, sticky="e", pady=8)
    captcha_mode = tk.StringVar(value="manual")
    captcha_frame = tk.Frame(input_frame)
    captcha_frame.grid(row=5, column=1, sticky="w")
    
    tk.Radiobutton(
        captcha_frame,
        text="手动输入",
        variable=captcha_mode,
        value="manual"
    ).pack(side=tk.LEFT, padx=(0, 10))
    tk.Radiobutton(
        captcha_frame,
        text="自动识别",
        variable=captcha_mode,
        value="auto"
    ).pack(side=tk.LEFT)
    
    # ===================== 日志区域 =====================
    log_frame = tk.Frame(frame)
    log_frame.grid(row=0, column=1, padx=10)
    
    tk.Label(log_frame, text="运行日志").pack()
    log_box = tk.Text(log_frame, width=42, height=18)
    log_box.pack()
    log(log_box, "日志已启动，等待操作...")
    
    # ===================== 验证码弹窗队列 =====================
    captcha_queue = queue.Queue()      # 存放 (image_bytes, result_queue)
    
    def check_captcha_queue():
        """在主线程中检查并显示验证码弹窗"""
        try:
            while True:
                image_bytes, result_queue = captcha_queue.get_nowait()
                # 在主线程显示弹窗（阻塞等待用户输入）
                result = show_captcha_dialog(window, image_bytes)
                # 将结果返回给爬取线程
                result_queue.put(result)
        except queue.Empty:
            pass
        # 每100ms检查一次
        window.after(100, check_captcha_queue)
    
    # 启动验证码检查循环
    window.after(100, check_captcha_queue)
    
    # ===================== 按钮事件 =====================
    def on_start_click():
        """开始爬取按钮点击事件"""
        keyword = key_entry.get().strip()
        start_date = start_entry.get().strip()
        end_date = end_entry.get().strip()
        pages = page_entry.get().strip()
        clean_enabled = clean_var.get()
        mode = captcha_mode.get()
        
        # 验证输入
        errors = validate_inputs(keyword, start_date, end_date, pages)
        if errors:
            messagebox.showerror("输入错误", "\n".join(errors))
            return
        
        # 禁用按钮
        start_button.config(state="disabled")
        log(log_box, "=" * 50)
        log(log_box, "开始爬取...")
        log(log_box, f"验证码模式: {'手动输入' if mode == 'manual' else '自动识别'}")
        
        # 后台线程运行爬取
        def crawl_thread():
            try:
                crawler = Crawler(captcha_mode=mode)
                
                # 验证码回调：将图片放入队列，等待主线程显示弹窗
                def captcha_callback(image_bytes):
                    result_queue = queue.Queue()
                    # 将任务放入队列
                    captcha_queue.put((image_bytes, result_queue))
                    # 阻塞等待主线程返回结果
                    result = result_queue.get(timeout=120)
                    return result
                
                crawler.set_captcha_callback(captcha_callback)
                
                article_data, all_content = crawler.crawl(
                    keyword=keyword,
                    start_date=start_date,
                    end_date=end_date,
                    max_page=int(pages),
                    clean_enabled=clean_enabled,
                    log_box=log_box
                )
                
                # 在主线程保存结果
                window.after(0, lambda: save_results(article_data, all_content))
                
            except Exception as e:
                window.after(0, lambda: handle_error(str(e)))
        
        def handle_error(error_msg):
            log(log_box, f"爬取失败：{error_msg}")
            messagebox.showerror("错误", f"爬取过程中发生错误：{error_msg}")
            try:
                start_button.config(state="normal")
            except:
                pass
        
        thread = threading.Thread(target=crawl_thread, daemon=True)
        thread.start()
    
    def save_results(article_data, all_content):
        """保存爬取结果到文件"""
        try:
            with open(OUTLINE_FILENAME, "w", encoding="utf-8") as f:
                for title, link, date, keywords in article_data:
                    f.write(f"标题：{title}\n")
                    f.write(f"链接：{link}\n")
                    f.write(f"日期：{date}\n")
                    f.write(f"关键词：{keywords}\n\n")
            
            with open(CONTENTS_FILENAME, "w", encoding="utf-8") as f:
                f.write(all_content)
            
            log(log_box, "✅ 全部完成！已保存 outline.txt 和 contents.txt")
            messagebox.showinfo("完成", "爬取完毕！请检查输出数据")
            
        except Exception as e:
            log(log_box, f"保存文件失败：{str(e)}")
            messagebox.showerror("错误", f"保存文件失败：{str(e)}")
        finally:
            try:
                start_button.config(state="normal")
            except:
                pass
    
    # 开始按钮
    start_button = ttk.Button(
        input_frame,
        text="开始爬取",
        command=on_start_click
    )
    start_button.grid(row=6, column=1, pady=15)
    
    window.mainloop()
