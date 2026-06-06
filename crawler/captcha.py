"""
验证码处理模块
支持自动检测、识别和提交验证码

依赖：ddddocr（可选，未安装时降级为手动输入模式）
"""

import requests
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
from bs4 import BeautifulSoup
import time
import os

# 尝试导入 ddddocr，失败时提供降级方案
try:
    import ddddocr
    DDDDOCR_AVAILABLE = True
except ImportError:
    DDDDOCR_AVAILABLE = False
    print("[警告] ddddocr 未安装或加载失败，验证码功能将使用手动输入模式")
    print("如需自动识别，请安装: pip install ddddocr")


class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self, mode="manual"):
        self.mode = mode
        self.ocr = None
        
        if mode == "auto" and DDDDOCR_AVAILABLE:
            try:
                self.ocr = ddddocr.DdddOcr(show_ad=False)
                print("[信息] 验证码自动识别模式已启用")
            except Exception as e:
                print(f"[警告] ddddocr 初始化失败: {e}")
    
    def set_mode(self, mode):
        self.mode = mode
        if mode == "auto" and DDDDOCR_AVAILABLE and not self.ocr:
            try:
                self.ocr = ddddocr.DdddOcr(show_ad=False)
            except:
                pass
    
    def detect_captcha_page(self, response_text):
        """检测响应是否为验证码页面"""
        return "请输入验证码" in response_text or "看不清楚" in response_text
    
    def extract_captcha_image(self, soup, base_url, session, log_box=None):
        """
        从验证码页面提取验证码图片
        已知HTML结构：
          <img src="/servlet/validateCodeServlet?loginName=" class="mid validateCode"/>
          <input type="text" id="validateCode" name="validateCode" .../>
          <form id="login_form" action="/member/validateCode" method="post">
        """
        # 方法1：精确匹配已知结构
        img = soup.find("img", class_="validateCode")
        if img and img.get("src"):
            img_url = img["src"]
            img_bytes = self._download_image(img_url, base_url, session)
            if img_bytes:
                return img_bytes, img_url
        
        # 方法2：匹配 validateCodeServlet
        img = soup.find("img", src=re.compile(r"validateCodeServlet", re.I))
        if img and img.get("src"):
            img_url = img["src"]
            img_bytes = self._download_image(img_url, base_url, session)
            if img_bytes:
                return img_bytes, img_url
        
        # 方法3：CSS选择器
        for selector in [
            "img[src*='captcha']", "img[src*='verify']", "img[src*='code']",
            "img[src*='rand']", "img[src*='servlet']", "img[src*='image']",
            "#imgCode", ".validateCode",
        ]:
            img_tag = soup.select_one(selector)
            if img_tag and img_tag.get("src"):
                img_bytes = self._download_image(img_tag["src"], base_url, session)
                if img_bytes:
                    return img_bytes, img_tag["src"]
        
        # 方法4：遍历所有img
        all_imgs = soup.find_all("img")
        for img in all_imgs:
            src = img.get("src", "")
            if src:
                img_bytes = self._download_image(src, base_url, session)
                if img_bytes:
                    return img_bytes, src
        
        return None, None
    
    def _download_image(self, img_url, base_url, session):
        """下载图片"""
        if img_url.startswith('/'):
            img_url = base_url + img_url
        elif not img_url.startswith('http'):
            img_url = base_url + '/' + img_url
        
        try:
            resp = session.get(img_url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 100:
                return resp.content
        except Exception as e:
            print(f"[调试] 图片下载异常: {e}")
        
        return None
    
    def preprocess_image(self, image_bytes):
        """预处理验证码图片"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            width, height = img.size
            if width < 200:
                scale = 3
            elif width < 400:
                scale = 2
            else:
                scale = 1.5
            
            new_size = (int(width * scale), int(height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
            img = img.filter(ImageFilter.MedianFilter(size=3))
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        except Exception as e:
            print(f"图片预处理失败: {e}")
            return image_bytes
    
    def recognize_captcha(self, image_bytes):
        """识别验证码"""
        if not self.ocr:
            return None
        try:
            processed = self.preprocess_image(image_bytes)
            result = self.ocr.classification(processed)
            cleaned = ''.join(c for c in result if c.isalnum())
            return cleaned.upper()
        except Exception as e:
            print(f"验证码识别失败: {e}")
            return None
    
    def submit_captcha(self, soup, session, captcha_code, base_url):
        """
        提交验证码
        已知表单结构：
          <form id="login_form" action="/member/validateCode" method="post">
            <input type="text" id="validateCode" name="validateCode" .../>
            <input type="submit" class="login_sub" value="提交"/>
          </form>
        """
        # 查找表单
        form = soup.find("form", id="login_form") or soup.find("form")
        if not form:
            print("未找到验证码表单")
            return None
        
        # 收集表单数据
        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            input_type = input_tag.get("type", "text")
            
            if name and input_type != "submit":
                data[name] = value
        
        # 填入验证码（已知字段名为 validateCode）
        captcha_field = form.find("input", {"name": "validateCode"})
        if captcha_field:
            data["validateCode"] = captcha_code
        else:
            # 通用匹配
            for key in list(data.keys()):
                if any(kw in key.lower() for kw in ['captcha', 'verify', 'code', 'validate']):
                    data[key] = captcha_code
                    break
        
        # 确定提交URL
        action = form.get("action", "")
        if action.startswith('/'):
            submit_url = base_url + action
        elif not action.startswith('http'):
            submit_url = base_url + '/' + action
        else:
            submit_url = action
        
        # 提交
        method = form.get("method", "POST").upper()
        try:
            if method == 'POST':
                resp = session.post(submit_url, data=data, timeout=15)
            else:
                resp = session.get(submit_url, params=data, timeout=15)
            return resp
        except Exception as e:
            print(f"提交验证码失败: {e}")
            return None
    
    def handle_with_retry(self, response, session, base_url, max_retry=3,
                         manual_callback=None, log_box=None):
        """带重试的验证码处理"""
        for attempt in range(max_retry):
            msg = f"验证码处理尝试 {attempt + 1}/{max_retry}"
            print(msg)
            if log_box:
                log(log_box, msg)
            
            soup = BeautifulSoup(response.text, "html.parser")
            image_bytes, img_url = self.extract_captcha_image(soup, base_url, session)
            
            if not image_bytes:
                msg = "无法获取验证码图片"
                print(msg)
                if log_box:
                    log(log_box, msg)
                return False, response
            
            msg = f"获取到验证码图片: {img_url}"
            print(msg)
            if log_box:
                log(log_box, msg)
            
            if self.mode == "auto" and self.ocr:
                # 自动模式
                msg = "[模式] 自动识别"
                print(msg)
                if log_box:
                    log(log_box, msg)
                
                code = self.recognize_captcha(image_bytes)
                if code:
                    msg = f"自动识别结果: {code}"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                    
                    new_resp = self.submit_captcha(soup, session, code, base_url)
                    if new_resp and not self.detect_captcha_page(new_resp.text):
                        msg = "自动识别验证通过"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                        return True, new_resp
                    else:
                        msg = "自动识别验证失败"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                else:
                    msg = "自动识别失败"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                
                # 自动失败，切换手动
                if manual_callback:
                    msg = "自动识别失败，切换到手动输入"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                    code = manual_callback(image_bytes)
                    if code:
                        msg = f"用户输入验证码: {code}"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                        new_resp = self.submit_captcha(soup, session, code, base_url)
                        if new_resp and not self.detect_captcha_page(new_resp.text):
                            msg = "手动输入验证通过"
                            print(msg)
                            if log_box:
                                log(log_box, msg)
                            return True, new_resp
                        else:
                            msg = "手动输入验证失败"
                            print(msg)
                            if log_box:
                                log(log_box, msg)
                    else:
                        msg = "用户取消输入"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                        return False, response
            else:
                # 手动模式
                msg = "[模式] 手动输入"
                print(msg)
                if log_box:
                    log(log_box, msg)
                
                if manual_callback:
                    msg = "弹出验证码输入窗口..."
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                    code = manual_callback(image_bytes)
                    if code:
                        msg = f"用户输入验证码: {code}"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                        new_resp = self.submit_captcha(soup, session, code, base_url)
                        if new_resp and not self.detect_captcha_page(new_resp.text):
                            msg = "验证码验证通过"
                            print(msg)
                            if log_box:
                                log(log_box, msg)
                            return True, new_resp
                        else:
                            msg = "验证码验证失败"
                            print(msg)
                            if log_box:
                                log(log_box, msg)
                    else:
                        msg = "用户取消输入"
                        print(msg)
                        if log_box:
                            log(log_box, msg)
                        return False, response
                else:
                    msg = "错误：未设置验证码回调函数"
                    print(msg)
                    if log_box:
                        log(log_box, msg)
                    return False, response
            
            if attempt < max_retry - 1:
                time.sleep(1)
                try:
                    response = session.get(response.url, timeout=15)
                except:
                    pass
        
        msg = "验证码处理失败，已达到最大重试次数"
        print(msg)
        if log_box:
            log(log_box, msg)
        return False, response
