#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备类型更新脚本
用于更新现有设备的设备类型
"""

import os
import sys
from datetime import datetime

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

print("开始更新设备类型...")

try:
    # 初始化Flask应用
    from src.app import app, db
    from src.modules.device.models import Device, DeviceType, init_device_types
    
    with app.app_context():
        # 确保基本设备类型存在
        init_device_types()
        
        # 获取所有设备类型
        device_types = DeviceType.query.all()
        if not device_types:
            print("错误：没有找到设备类型，请确保设备类型已初始化")
            sys.exit(1)
        
        # 为方便选择，创建设备类型字典
        device_type_dict = {dt.id: dt.name for dt in device_types}
        
        # 获取所有没有设备类型的设备
        devices_without_type = Device.query.filter(Device.type_id.is_(None)).all()
        
        if not devices_without_type:
            print("所有设备已经有设备类型，无需更新")
            sys.exit(0)
        
        print(f"找到 {len(devices_without_type)} 个没有设备类型的设备")
        
        # 创建默认设备类型映射
        default_type_mapping = {
            # 根据设备名称中的关键字映射设备类型
            "服务器": next((dt.id for dt in device_types if dt.name == "服务器"), None),
            "网络": next((dt.id for dt in device_types if dt.name == "网络设备"), None),
            "交换机": next((dt.id for dt in device_types if dt.name == "网络设备"), None),
            "路由器": next((dt.id for dt in device_types if dt.name == "网络设备"), None),
            "防火墙": next((dt.id for dt in device_types if dt.name == "安全设备"), None),
            "摄像头": next((dt.id for dt in device_types if dt.name == "监控设备"), None),
            "监控": next((dt.id for dt in device_types if dt.name == "监控设备"), None),
            "工作站": next((dt.id for dt in device_types if dt.name == "终端设备"), None),
            "终端": next((dt.id for dt in device_types if dt.name == "终端设备"), None),
        }
        
        # 如果找不到合适的设备类型，使用"其他"类型
        other_type_id = next((dt.id for dt in device_types if dt.name == "其他"), None)
        
        # 自动更新设备类型
        updated_count = 0
        for device in devices_without_type:
            # 尝试根据设备名称自动识别设备类型
            assigned_type_id = None
            for keyword, type_id in default_type_mapping.items():
                if keyword in device.name.lower():
                    assigned_type_id = type_id
                    break
            
            # 如果无法自动识别，使用"其他"类型
            if not assigned_type_id and other_type_id:
                assigned_type_id = other_type_id
            
            # 更新设备类型
            if assigned_type_id:
                device.type_id = assigned_type_id
                updated_count += 1
                print(f"已将设备 {device.name} 的类型更新为 {device_type_dict.get(assigned_type_id, '未知')}")
        
        # 提交更改
        db.session.commit()
        print(f"成功更新了 {updated_count} 个设备的类型")
        
        # 检查是否还有未分配类型的设备
        remaining = Device.query.filter(Device.type_id.is_(None)).count()
        if remaining > 0:
            print(f"警告：仍有 {remaining} 个设备没有设备类型，请手动更新")
        else:
            print("所有设备都已分配设备类型")
        
except Exception as e:
    print(f"更新设备类型时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("设备类型更新完成") 