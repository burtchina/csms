#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
维护管理相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

# 创建蓝图
maintenance_bp = Blueprint('maintenance', __name__)

# 维护记录列表
@maintenance_bp.route('/')
@login_required
def index():
    return render_template('maintenance/index.html') 