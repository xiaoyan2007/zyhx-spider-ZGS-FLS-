"""
项目配置文件
集中管理所有常量、配置项
"""

import os
import sys

# ===================== 路径配置 =====================
def get_icon_path():
    """自动获取图标路径（打包兼容）"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "logo.ico")
    return "logo.ico"


# ===================== 网络请求配置 =====================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://data.people.com.cn/",
    "Connection": "keep-alive"
}

BASE_URL = "http://data.people.com.cn"
TIMEOUT = 15
RETRY_TIMES = 3
DELAY_BETWEEN_PAGES = 1.0      # 页间延迟（秒）
DELAY_BETWEEN_ARTICLES = 0.8   # 文章间延迟（秒）


# ===================== 内容过滤配置 =====================
EXCLUDE_TEXT = [
    "《 人民日报 》",
    "分享让更多人看到",
    "人民日报",
    "登录人民网",
    "版权所有"
]


# ===================== 输出配置 =====================
OUTPUT_DIR = "."
OUTLINE_FILENAME = "outline.txt"
CONTENTS_FILENAME = "contents.txt"


# ===================== GUI 配置 =====================
WINDOW_TITLE = "智宇慧轩爬虫 Beta 0.2 作者：ZGSU-FLS-Tony"
WINDOW_SIZE = "900x500"

DISCLAIMER_TITLE = "免责与合规声明"
DISCLAIMER_SIZE = "620x520"

ZJGSU_LIBRARY_URL = "https://lib.zjgsu.edu.cn/1020/list.htm"


# ===================== 免责声明文本 =====================
DISCLAIMER_TEXT = """智宇慧轩爬虫 —— 法律免责与合规使用声明

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
程序可能因目标网站改版导致解析异常，使用者需自行核验数据有效性。"""
