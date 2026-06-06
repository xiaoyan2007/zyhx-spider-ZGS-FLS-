"""
验证码输入弹窗模块
显示验证码图片并提供输入框
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import io


class CaptchaDialog:
    """验证码输入对话框"""
    
    def __init__(self, parent, image_bytes):
        """
        初始化验证码对话框
        
        Args:
            parent: 父窗口
            image_bytes: 验证码图片二进制数据
        """
        self.parent = parent
        self.image_bytes = image_bytes
        self.result = None
        
        # 创建弹窗
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("请输入验证码")
        self.dialog.geometry("420x320")
        self.dialog.resizable(False, False)
        
        # 模态窗口
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 窗口关闭时处理
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 320) // 2
        self.dialog.geometry(f"420x320+{x}+{y}")
        
        # 构建界面
        self._build_ui()
        
        # 聚焦输入框
        self.entry.focus_set()
    
    def _build_ui(self):
        """构建界面元素"""
        # 标题
        tk.Label(
            self.dialog,
            text="⚠ 检测到验证码",
            font=("微软雅黑", 14, "bold"),
            fg="#d9534f"
        ).pack(pady=(15, 5))
        
        # 说明文字
        tk.Label(
            self.dialog,
            text="请识别下方图片中的验证码并输入",
            font=("微软雅黑", 10)
        ).pack()
        
        # 验证码图片
        self._show_captcha_image()
        
        # 输入区域
        input_frame = tk.Frame(self.dialog)
        input_frame.pack(pady=8)
        
        tk.Label(
            input_frame,
            text="验证码：",
            font=("微软雅黑", 11)
        ).pack(side=tk.LEFT)
        
        self.entry = ttk.Entry(
            input_frame,
            width=15,
            font=("Consolas", 16),
            justify="center"
        )
        self.entry.pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        self.entry.bind("<Return>", lambda e: self._on_submit())
        
        # 按钮区域
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=8)
        
        submit_btn = tk.Button(
            btn_frame,
            text="提  交",
            command=self._on_submit,
            width=10,
            bg="#28a745",
            fg="white",
            font=("微软雅黑", 10)
        )
        submit_btn.pack(side=tk.LEFT, padx=8)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="取  消",
            command=self._on_cancel,
            width=10,
            font=("微软雅黑", 10)
        )
        cancel_btn.pack(side=tk.LEFT, padx=8)
        
        # 提示文字
        tk.Label(
            self.dialog,
            text="提示：验证码区分大小写，输入后按回车或点击提交",
            font=("微软雅黑", 9),
            fg="gray"
        ).pack(pady=5)
    
    def _show_captcha_image(self):
        """显示验证码图片"""
        try:
            image = Image.open(io.BytesIO(self.image_bytes))
            
            max_width = 350
            max_height = 80
            
            width, height = image.size
            ratio = min(max_width / width, max_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            
            if new_size[0] > 0 and new_size[1] > 0:
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(image)
            
            img_frame = tk.Frame(self.dialog, bd=2, relief="groove")
            img_frame.pack(pady=8)
            
            label = tk.Label(img_frame, image=self.photo, bg="white")
            label.pack(padx=2, pady=2)
            
        except Exception as e:
            print(f"显示验证码图片失败: {e}")
            tk.Label(
                self.dialog,
                text=f"[图片加载失败: {e}]",
                font=("微软雅黑", 12),
                fg="red"
            ).pack(pady=10)
    
    def _on_submit(self):
        """提交按钮点击事件"""
        code = self.entry.get().strip()
        if code:
            self.result = code.upper()
            self.dialog.destroy()
        else:
            self._shake_window()
    
    def _on_cancel(self):
        """取消按钮点击事件"""
        self.result = None
        self.dialog.destroy()
    
    def _shake_window(self):
        """窗口震动效果"""
        x = self.dialog.winfo_x()
        y = self.dialog.winfo_y()
        
        for _ in range(3):
            self.dialog.geometry(f"+{x + 5}+{y}")
            self.dialog.update()
            self.dialog.after(50)
            self.dialog.geometry(f"+{x - 5}+{y}")
            self.dialog.update()
            self.dialog.after(50)
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def show_and_wait(self):
        """
        显示弹窗并等待用户操作
        阻塞直到用户提交或取消
        
        Returns:
            用户输入的验证码，取消返回None
        """
        self.dialog.wait_window()
        return self.result


def show_captcha_dialog(parent, image_bytes):
    """
    显示验证码输入对话框并等待用户输入
    
    Args:
        parent: 父窗口
        image_bytes: 验证码图片二进制数据
        
    Returns:
        用户输入的验证码，取消返回None
    """
    dialog = CaptchaDialog(parent, image_bytes)
    return dialog.show_and_wait()
