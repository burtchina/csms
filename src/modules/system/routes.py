#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统管理相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

# 创建蓝图
system_bp = Blueprint('system', __name__)

# 系统设置主页
@system_bp.route('/')
@login_required
def index():
    return render_template('system/index.html') 