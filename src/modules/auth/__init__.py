#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证模块初始化
"""
from flask import Blueprint

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, template_folder='templates')

# 导入路由
from src.modules.auth import routes 