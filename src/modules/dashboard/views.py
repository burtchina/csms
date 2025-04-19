#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
仪表板模块视图 - 导出蓝图
"""

from src.modules.dashboard import dashboard_bp

# 导出蓝图供app.py使用
__all__ = ['dashboard_bp'] 