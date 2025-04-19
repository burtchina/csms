"""
设备模块视图 - 导出蓝图
"""

from src.core.db import db
from src.modules.device import device_bp

# 导出蓝图供app.py使用
__all__ = ['device_bp'] 