#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
仪表板模块路由
"""

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from src.modules.dashboard import dashboard_bp
from src.models import Device

@dashboard_bp.route('/')
@login_required
def index():
    """仪表板首页 - 系统概览"""
    # 获取设备总数
    device_count = Device.query.count()
    
    # 获取各种状态的设备数量
    normal_count = Device.query.filter_by(status='正常').count()
    maintenance_count = Device.query.filter_by(status='维修中').count()
    inactive_count = Device.query.filter_by(status='闲置').count()
    retired_count = Device.query.filter_by(status='报废').count()
    
    # 获取最近添加的设备
    recent_devices = Device.query.order_by(Device.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard/index.html',
        title="系统仪表板",
        device_count=device_count,
        normal_count=normal_count,
        maintenance_count=maintenance_count,
        inactive_count=inactive_count,
        retired_count=retired_count,
        recent_devices=recent_devices
    ) 