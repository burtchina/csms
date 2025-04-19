#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
显示设备数据脚本
此脚本用于显示设备表的数据，帮助分析问题
"""

import os
import sys
import json
from datetime import datetime

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

print("读取设备数据...")

try:
    # 初始化Flask应用
    from src.app import app, db
    from src.modules.device.models import Device, DeviceType
    
    with app.app_context():
        # 获取设备类型字典，便于显示
        device_types = DeviceType.query.all()
        type_dict = {dt.id: dt.name for dt in device_types}
        
        # 获取所有设备
        devices = Device.query.all()
        print(f"系统中共有 {len(devices)} 个设备")
        
        print("\n设备表结构:")
        # 显示设备模型的字段
        for column in Device.__table__.columns:
            print(f"- {column.name}: {column.type} (nullable: {column.nullable})")
        
        print("\n设备数据:")
        for device in devices:
            # 构建一个包含所有字段的字典
            device_data = {
                'id': device.id,
                'name': device.name,
                'device_code': device.device_code,
                'type_id': device.type_id,
                'type_name': type_dict.get(device.type_id, 'Unknown'),
                'location': device.location,
                'ip_address': device.ip_address, 
                'status': device.status,
                'status_repr': repr(device.status),  # 显示原始表示
                'status_type': type(device.status).__name__,  # 显示类型
                'status_len': len(device.status) if device.status else 0  # 显示长度
            }
            
            # 输出设备数据，美化格式
            print(f"\n设备 {device.id}: {device.name}")
            for key, value in device_data.items():
                print(f"  {key}: {value}")
        
except Exception as e:
    print(f"读取设备数据时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n设备数据读取完成") 