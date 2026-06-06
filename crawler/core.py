"""
爬虫核心模块
负责文章列表获取和正文内容爬取
"""

import requests
import urllib.parse
import json
import time
import tkinter as tk
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import HEADERS, BASE_URL, TIMEOUT, EXCLUDE_TEXT
from config import DELAY_BETWEEN_PAGES, DELAY_BETWEEN_ARTICLES
from utils.logger import log
from .captcha import CaptchaHandler


class Crawler:
    """人民日报爬虫类"""
    
    def __init__(self, captcha_mode="manual"):
        """
        初始化爬虫
        
        Args:
            captcha_mode: 验证码处理模式，"manual"为手动输入，"auto"为自动识别
        """
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.captcha_handler = CaptchaHandler(mode=captcha_mode)
        self.captcha_callback = None
        self.request_count = 0
        self.last_request_time = 0
    
    def set_captcha_callback(self, callback):
        """
        设置验证码手动输入回调函数
        
        Args:
            callback: 接收图片bytes，返回用户输入的验证码字符串
        """
        self.captcha_callback = callback
    
    def set_captcha_mode(self, mode):
        """切换验证码处理模式"""
        self.captcha_handler.set_mode(mode)
    
    def _smart_delay(self):
        """智能延迟，随请求次数增加延迟"""
        self.request_count += 1
        
        import random
        base_delay = 1.5
        if self.request_count > 20:
            base_delay = 2.5
        if self.request_count > 50:
            base_delay = 4.0
        
        jitter = random.uniform(0.5, 2.0)
        delay = base_delay + jitter
        
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url, method='GET', data=None, log_box=None):
        """
        发送请求并自动处理验证码
        
        Args:
            url: 请求URL
            method: 请求方法
            data: POST数据
            log_box: 日志文本框
            
        Returns:
            Response对象
        """
        self._smart_delay()
        
        try:
            if method.upper() == 'POST':
                resp = self.session.post(url, data=data, timeout=TIMEOUT)
            else:
                resp = self.session.get(url, timeout=TIMEOUT)
            
            # 检测是否触发验证码
            if self.captcha_handler.detect_captcha_page(resp.text):
                mode_str = "自动识别" if self.captcha_handler.mode == "auto" else "手动输入"
                msg = f"检测到验证码，当前模式: {mode_str}"
                print(msg)
                if log_box:
                    log(log_box, msg)
                
                # 调试：保存验证码页面HTML
                try:
                    debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "captcha_debug.html")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    dbg_msg = f"[调试] 验证码页面已保存到: {debug_path}"
                    print(dbg_msg)
                    if log_box:
                        log(log_box, dbg_msg)
                except Exception as dbg_e:
                    print(f"[调试] 保存HTML失败: {dbg_e}")
                
                success, new_resp = self.captcha_handler.handle_with_retry(
                    resp, self.session, BASE_URL,
                    manual_callback=self.captcha_callback,
                    log_box=log_box
                )
                
                if success:
                    msg = "验证码验证通过，继续爬取"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                    return new_resp
                else:
                    msg = "验证码验证失败，跳过当前请求"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
            
            return resp
            
        except Exception as e:
            raise e
    
    def _build_search_url(self, keyword: str, start_date: str, end_date: str, page: int) -> str:
        """
        构建搜索URL
        
        Args:
            keyword: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            
        Returns:
            完整的搜索URL
        """
        query_structure = {
            "cds": [
                {"fld": "dataTime.start", "cdr": "AND", "val": start_date},
                {"fld": "dataTime.end", "cdr": "AND", "val": end_date},
                {"cdr": "AND", "cds": [
                    {"fld": "title", "cdr": "OR", "val": keyword},
                    {"fld": "subTitle", "cdr": "OR", "val": keyword}
                ]}
            ],
            "obs": [{"fld": "dataTime", "drt": "DESC"}],
            "tr": "A",
            "ss": "1",
            "pageNo": page,
            "pageSize": 20
        }
        qs_str = urllib.parse.quote(json.dumps(query_structure))
        return f"{BASE_URL}/rmrb/s?qs={qs_str}"
    
    def get_article_content(self, url: str, log_box=None) -> str:
        """
        获取文章正文内容
        
        Args:
            url: 文章链接
            log_box: 日志文本框（可选）
            
        Returns:
            清洗后的文章正文，失败返回空字符串
        """
        try:
            res = self._make_request(url, log_box=log_box)
            
            # 编码检测
            try:
                res.content.decode("gbk")
                res.encoding = "gbk"
            except UnicodeDecodeError:
                res.encoding = "utf-8"
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 尝试定位主要内容区域
            content_div = (
                soup.find('div', class_='text_con') or
                soup.find('div', class_='content') or
                soup.find('article')
            )
            
            if content_div:
                p_list = content_div.find_all("p")
            else:
                p_list = soup.find_all("p")
            
            # 提取并清洗文本
            texts = []
            for p in p_list:
                text = p.get_text(strip=True)
                if text:
                    # 过滤排除文本
                    for ban_str in EXCLUDE_TEXT:
                        text = text.replace(ban_str, "")
                    if text.strip():
                        texts.append(text)
            
            return "\n".join(texts)
            
        except Exception as e:
            log_text = f"获取文章失败 {url}: {str(e)}"
            print(log_text)
            return ""
    
    def get_outline_list(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        max_page: int,
        log_box: tk.Text
    ) -> List[Tuple[str, str, str, str]]:
        """
        获取文章目录列表
        
        Args:
            keyword: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            max_page: 最大爬取页数
            log_box: 日志输出文本框
            
        Returns:
            文章信息列表，每项为 (标题, 链接, 日期, 关键词)
        """
        article_list = []
        page = 1
        
        while page <= max_page:
            log(log_box, f"正在抓取第 {page} 页目录...")
            
            url = self._build_search_url(keyword, start_date, end_date, page)
            
            try:
                resp = self._make_request(url, log_box=log_box)
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
                    link = f"{BASE_URL}{h3_a['href']}"
                    date = date_tag.get_text(strip=True)
                    keywords = ",".join([k.get_text(strip=True) for k in kw_tags])
                    
                    article_list.append((title, link, date, keywords))
                    log(log_box, f"已抓取文章：{title}")
                
                page += 1
                # 智能延迟已在 _make_request 中处理
                
            except Exception as err:
                log(log_box, f"目录抓取异常：{str(err)}")
                break
        
        return article_list
    
    def crawl(
        self,
        keyword: str,
        start_date: str,
        end_date: str,
        max_page: int,
        clean_enabled: bool,
        log_box: tk.Text
    ) -> Tuple[List[Tuple], str]:
        """
        执行完整爬取流程
        
        Args:
            keyword: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            max_page: 最大页数
            clean_enabled: 是否启用语料清洗
            log_box: 日志输出文本框
            
        Returns:
            (文章列表, 合并后的正文内容)
        """
        # 重置计数器
        self.request_count = 0
        self.last_request_time = 0
        
        # 获取文章列表
        article_data = self.get_outline_list(
            keyword, start_date, end_date, max_page, log_box
        )
        log(log_box, f"共获取到 {len(article_data)} 篇文章")
        
        # 抓取正文
        all_content = ""
        for idx, (title, url, date, kw) in enumerate(article_data):
            log(log_box, f"正在抓取正文 {idx + 1}/{len(article_data)}")
            content = self.get_article_content(url, log_box=log_box)
            
            if clean_enabled:
                # 清洗模式：去空格/换行，合成一段
                content = ''.join(content.split())
                all_content += content + "\n"
            else:
                # 阅读模式：保留格式，添加文章标题
                all_content += f"【文章{idx + 1}】\n{content}\n"
            
            # 智能延迟已在 _make_request 中处理
        
        return article_data, all_content.strip()
