#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证模块视图 - 导出蓝图
"""

from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# 从routes模块导入所有路由
from src.modules.auth import routes

# 导出蓝图供app.py使用
__all__ = ['auth_bp'] 