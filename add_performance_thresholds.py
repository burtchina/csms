#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
为设备添加更多性能阈值数据，包括内存和带宽使用率的阈值
"""

from src.app import create_app
from src.models import Threshold
from src.models.device import Device
from src.core.db import db

def add_threshold(device_id, metric_name, warning, critical):
    """添加阈值设置，如果已存在则跳过"""
    # 检查是否已存在相同设备和指标的阈值
    existing = Threshold.query.filter_by(device_id=device_id, metric_name=metric_name).first()
    if existing:
        print(f"设备ID {device_id} 的 {metric_name} 阈值已存在，跳过添加")
        return
    
    # 创建新阈值
    new_threshold = Threshold(
        device_id=device_id,
        metric_name=metric_name,
        warning_threshold=warning,
        critical_threshold=critical
    )
    
    db.session.add(new_threshold)
    print(f"为设备ID {device_id} 添加 {metric_name} 阈值：警告={warning}%, 严重={critical}%")

def main():
    app = create_app()
    
    with app.app_context():
        # 获取所有设备
        devices = Device.query.all()
        
        if not devices:
            print("没有找到设备")
            return
        
        print(f"找到 {len(devices)} 个设备，准备添加阈值数据...")
        
        try:
            # 为每个设备添加内存和带宽使用率阈值
            for device in devices:
                # 内存使用率阈值
                add_threshold(device.id, "memory_usage", 75.0, 90.0)
                
                # 带宽使用率阈值
                add_threshold(device.id, "bandwidth_usage", 70.0, 85.0)
            
            # 提交所有更改
            db.session.commit()
            print("阈值数据添加成功")
            
            # 显示所有阈值设置
            thresholds = Threshold.query.all()
            print(f"\n当前阈值设置 ({len(thresholds)}):")
            for t in thresholds:
                metric_name_map = {
                    "cpu_usage": "CPU使用率",
                    "memory_usage": "内存使用率",
                    "bandwidth_usage": "带宽使用率"
                }
                device_name = Device.query.get(t.device_id).name
                metric_display = metric_name_map.get(t.metric_name, t.metric_name)
                print(f"设备: {device_name}, 指标: {metric_display}, 警告: {t.warning_threshold}%, 严重: {t.critical_threshold}%")
        
        except Exception as e:
            db.session.rollback()
            print(f"添加阈值数据失败: {str(e)}")

if __name__ == "__main__":
    main() 