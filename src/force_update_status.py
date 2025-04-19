#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
强制更新设备状态脚本
强制将所有设备的状态设置为'正常'
"""

import os
import sys

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

print("开始强制更新设备状态...")

try:
    # 初始化Flask应用
    from src.app import app, db
    from src.modules.device.models import Device
    
    with app.app_context():
        # 获取所有设备
        devices = Device.query.all()
        print(f"系统中共有 {len(devices)} 个设备")
        
        # 强制更新所有设备的状态
        for device in devices:
            old_status = device.status
            device.status = "正常"
            print(f"设备 {device.id}:{device.name} 的状态从 '{old_status}' 更新为 '正常'")
        
        # 提交更改
        db.session.commit()
        print(f"成功更新了 {len(devices)} 个设备的状态")
        
except Exception as e:
    print(f"更新设备状态时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("设备状态强制更新完成") 