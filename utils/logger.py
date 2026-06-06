"""
日志工具模块
提供GUI日志输出和文件日志记录功能
"""

import tkinter as tk
import logging
import logging.handlers


def log(text_widget: tk.Text, msg: str) -> None:
    """
    在GUI文本框中输出日志
    
    Args:
        text_widget: tkinter Text控件
        msg: 要输出的日志消息
    """
    text_widget.insert(tk.END, msg + "\n")
    text_widget.see(tk.END)
    text_widget.update()


def setup_logger(name: str = "crawler", log_file: str = "crawler.log") -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志器名称
        log_file: 日志文件路径
        
    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件日志（轮转，最大10MB，保留5个备份）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
