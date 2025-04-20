#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查设备数据库信息
"""

import os
import sys

# 将项目根目录添加到Python路径中
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from src.app import create_app

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        # 导入模型
        from src.models.device import Device, DeviceType
        
        # 查询设备类型
        device_types = DeviceType.query.all()
        print(f"设备类型 ({len(device_types)}):")
        for dt in device_types:
            print(f"ID: {dt.id}, 名称: {dt.name}, 描述: {dt.description}")
        print("\n" + "-" * 80 + "\n")
        
        # 查询设备
        devices = Device.query.all()
        print(f"设备 ({len(devices)}):")
        for device in devices:
            type_name = device.type.name if device.type else "未知"
            print(f"ID: {device.id}, 名称: {device.name}, IP: {device.ip_address}, 类型: {type_name}")
            print(f"  连接信息: 用户名={device.username}, 密码={device.password}, 端口={device.port}")
            print(f"  状态: {device.status}, 位置: {device.location}")
            print("-" * 50)
        
        # 查询网络设备
        network_device_types = ['路由器', '交换机', '防火墙']
        network_devices = Device.query.join(Device.type).filter(
            DeviceType.name.in_(network_device_types)
        ).all()
        
        print(f"\n网络设备 ({len(network_devices)}):")
        for device in network_devices:
            print(f"ID: {device.id}, 名称: {device.name}, IP: {device.ip_address}, 类型: {device.type.name}")
            print(f"  连接信息: 用户名={device.username}, 密码={device.password}, 端口={device.port}")
            if not (device.username and device.password and device.ip_address):
                print("  警告: 缺少连接信息!")
            print("-" * 50)

if __name__ == "__main__":
    main() 