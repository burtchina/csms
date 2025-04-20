#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统管理相关路由
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
system_bp = Blueprint('system', __name__)

# 系统设置主页
@system_bp.route('/')
@login_required
def index():
    try:
        # 获取当前服务器时间
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template('system/index.html', now=now)
    except Exception as e:
        logger.error(f"访问系统设置页面出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('errors/500.html', message=f"加载系统设置页面出错: {str(e)}")

# 更新系统设置
@system_bp.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    try:
        # 获取表单数据
        alert_threshold = request.form.get('alert_threshold', type=int)
        data_retention = request.form.get('data_retention', type=int)
        
        # 这里添加保存配置的逻辑
        # ...
        
        flash('系统设置已更新', 'success')
        return redirect(url_for('system.index'))
    except Exception as e:
        logger.error(f"更新系统设置出错: {str(e)}")
        flash(f'更新系统设置失败: {str(e)}', 'danger')
        return redirect(url_for('system.index')) 