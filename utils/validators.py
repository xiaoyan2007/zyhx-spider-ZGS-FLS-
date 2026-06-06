"""
输入验证模块
提供各类输入参数的验证功能
"""

from datetime import datetime
from typing import List, Tuple


def validate_date(date_str: str) -> bool:
    """
    验证日期格式是否为 YYYY-MM-DD
    
    Args:
        date_str: 日期字符串
        
    Returns:
        格式正确返回True，否则返回False
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_inputs(keyword: str, start_date: str, end_date: str, pages: str) -> List[str]:
    """
    验证用户输入参数
    
    Args:
        keyword: 关键词
        start_date: 开始日期
        end_date: 结束日期
        pages: 爬取页数
        
    Returns:
        错误信息列表，空列表表示验证通过
    """
    errors = []
    
    if not keyword or not keyword.strip():
        errors.append("关键词不能为空")
    
    if not validate_date(start_date):
        errors.append("开始日期格式错误，应为 YYYY-MM-DD")
    
    if not validate_date(end_date):
        errors.append("结束日期格式错误，应为 YYYY-MM-DD")
    
    if validate_date(start_date) and validate_date(end_date):
        if start_date > end_date:
            errors.append("开始日期不能晚于结束日期")
    
    try:
        p = int(pages)
        if p < 1:
            errors.append("页数必须大于0")
        elif p > 100:
            errors.append("页数不能超过100")
    except ValueError:
        errors.append("页数必须是数字")
    
    return errors
