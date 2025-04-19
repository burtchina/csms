#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
仪表板模块初始化
"""
from flask import Blueprint

# 创建蓝图
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

# 导入路由
from src.modules.dashboard import routes 