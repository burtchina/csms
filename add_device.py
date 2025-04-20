#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
添加和更新设备信息的脚本
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
        from src.core.db import db
        
        # 1. 确保设备类型存在
        print("检查设备类型...")
        network_device_types = ['路由器', '交换机', '防火墙']
        for type_name in network_device_types:
            device_type = DeviceType.query.filter_by(name=type_name).first()
            if not device_type:
                print(f"添加设备类型: {type_name}")
                device_type = DeviceType(name=type_name, description=f"{type_name}设备")
                db.session.add(device_type)
        
        # 提交设备类型变更
        db.session.commit()
        
        # 2. 获取设备类型ID
        router_type = DeviceType.query.filter_by(name='路由器').first()
        switch_type = DeviceType.query.filter_by(name='交换机').first()
        firewall_type = DeviceType.query.filter_by(name='防火墙').first()
        
        # 3. 获取现有设备，并更新端口信息等
        print("更新现有设备信息...")
        devices = Device.query.all()
        for device in devices:
            if device.port is None:
                print(f"更新设备 {device.name} 的端口信息为22")
                device.port = 22
                
            # 确保其他必要字段存在
            if not device.username or not device.password:
                print(f"更新设备 {device.name} 的连接凭据")
                device.username = device.username or "admin"
                device.password = device.password or "Admin@123"
        
        # 4. 添加示例设备（如果没有足够的设备）
        if len(devices) < 3:
            print("添加示例设备...")
            
            # 添加路由器
            if not Device.query.filter_by(name="Router1").first():
                router = Device(
                    name="Router1",
                    ip_address="192.168.1.1",
                    type_id=router_type.id,
                    location="主机房",
                    status="正常",
                    model="AR2200",
                    firmware_version="V800R021C10",
                    username="admin",
                    password="Admin@123",
                    port=22
                )
                db.session.add(router)
                print("添加了路由器: Router1")
                
            # 添加交换机
            if not Device.query.filter_by(name="Switch1").first():
                switch = Device(
                    name="Switch1",
                    ip_address="192.168.1.2",
                    type_id=switch_type.id,
                    location="主机房",
                    status="正常",
                    model="S5700",
                    firmware_version="V200R010C00",
                    username="admin",
                    password="Admin@123",
                    port=22
                )
                db.session.add(switch)
                print("添加了交换机: Switch1")
                
            # 添加防火墙
            if not Device.query.filter_by(name="Firewall1").first():
                firewall = Device(
                    name="Firewall1",
                    ip_address="192.168.1.3",
                    type_id=firewall_type.id,
                    location="主机房",
                    status="正常",
                    model="USG6000",
                    firmware_version="V500R005C00",
                    username="admin",
                    password="Admin@123",
                    port=22
                )
                db.session.add(firewall)
                print("添加了防火墙: Firewall1")
        
        # 提交所有更改
        db.session.commit()
        print("设备信息更新完成！")
        
        # 显示更新后的设备信息
        print("\n更新后的设备信息:")
        devices = Device.query.all()
        for device in devices:
            type_name = device.type.name if device.type else "未知"
            print(f"ID: {device.id}, 名称: {device.name}, IP: {device.ip_address}, 类型: {type_name}")
            print(f"  连接信息: 用户名={device.username}, 密码={device.password}, 端口={device.port}")
            print(f"  状态: {device.status}, 位置: {device.location}")
            print("-" * 50)

if __name__ == "__main__":
    main() 