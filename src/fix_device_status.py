#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复设备状态脚本
此脚本专门用于修复设备的状态字段，确保没有空状态
"""

import os
import sys
from datetime import datetime

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

print("开始修复设备状态...")

try:
    # 初始化Flask应用
    from src.app import app, db
    from src.modules.device.models import Device
    
    with app.app_context():
        # 打印数据库连接信息
        print(f"数据库文件路径: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # 获取所有设备
        devices = Device.query.all()
        print(f"系统中共有 {len(devices)} 个设备")
        
        # 统计各种状态的设备数量
        status_count = {}
        for device in devices:
            status = device.status
            if not status:
                status = 'NULL'
            status_count[status] = status_count.get(status, 0) + 1
        
        print("当前设备状态统计:")
        for status, count in status_count.items():
            print(f"- {status}: {count}个")
        
        # 修复设备状态
        updated_count = 0
        for device in devices:
            # 检查设备状态是否为空
            if not device.status:
                device.status = '正常'
                updated_count += 1
                print(f"设备 {device.id}:{device.name} 的状态已更新为'正常'")
        
        # 如果有更新，提交到数据库
        if updated_count > 0:
            db.session.commit()
            print(f"成功更新了 {updated_count} 个设备的状态")
        else:
            print("没有发现需要更新状态的设备")
        
        # 验证所有设备都有状态
        devices_without_status = Device.query.filter((Device.status.is_(None)) | (Device.status == '')).count()
        if devices_without_status > 0:
            print(f"警告：仍有 {devices_without_status} 个设备没有状态")
        else:
            print("所有设备都已设置状态")
        
except Exception as e:
    print(f"修复设备状态时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("设备状态修复完成") 