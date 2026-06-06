"""
智宇慧轩爬虫 - 主入口

项目结构：
├── main.py              # 主入口（当前文件）
├── config.py            # 配置文件
├── crawler/             # 爬虫模块
│   ├── __init__.py
│   └── core.py          # 爬虫核心逻辑
├── gui/                 # 界面模块
│   ├── __init__.py
│   ├── disclaimer.py    # 免责声明弹窗
│   └── main_window.py   # 主界面
└── utils/               # 工具模块
    ├── __init__.py
    ├── logger.py        # 日志工具
    └── validators.py    # 输入验证

使用方法：
    python main.py
"""

import tkinter as tk
from gui import show_disclaimer_window, run_gui


def main():
    """程序主入口"""
    # 创建临时根窗口（用于支持多窗口）
    root_tmp = tk.Tk()
    root_tmp.withdraw()
    
    # 显示免责声明，同意后进入主界面
    show_disclaimer_window(on_agree_callback=run_gui)
    
    # 清理临时窗口
    root_tmp.destroy()


if __name__ == "__main__":
    main()
