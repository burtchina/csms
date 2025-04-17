#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
故障管理相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

# 创建蓝图
fault_bp = Blueprint('fault', __name__)

# 故障列表
@fault_bp.route('/')
@login_required
def index():
    return render_template('fault/index.html') 