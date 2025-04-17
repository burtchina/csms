#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能监控定时任务
"""

import logging
from datetime import datetime
from flask import current_app

from src.db import db
from src.core.models import Device
from src.modules.performance.services import PerformanceCollector

# 创建日志器
logger = logging.getLogger(__name__)

def schedule_performance_monitoring_tasks(scheduler):
    """
    注册性能监控相关的定时任务
    
    Args:
        scheduler: APScheduler实例
    """
    # 注册设备性能数据采集任务（每5分钟执行一次）
    scheduler.add_job(
        collect_performance_data,
        'interval',
        minutes=5,
        id='collect_performance_data',
        replace_existing=True,
        name='采集设备性能数据'
    )
    
    logger.info("已注册性能监控定时任务")

def collect_performance_data():
    """采集所有设备的性能数据"""
    with current_app.app_context():
        start_time = datetime.now()
        logger.info(f"开始采集设备性能数据，时间: {start_time}")
        
        # 获取所有正常状态的设备
        devices = Device.query.filter_by(status='正常').all()
        
        if not devices:
            logger.info("没有可用的设备，跳过性能数据采集")
            return
        
        success_count = 0
        failed_count = 0
        
        # 遍历所有设备采集性能数据
        for device in devices:
            try:
                logger.debug(f"正在采集设备 {device.name} (ID: {device.id}) 的性能数据")
                result = PerformanceCollector.collect_device_performance(device.id)
                
                if result['status'] == 'success':
                    success_count += 1
                    # 如果有告警，记录到日志
                    if result.get('alerts'):
                        for alert in result['alerts']:
                            logger.warning(f"设备告警: {device.name} - {alert['message']}")
                else:
                    failed_count += 1
                    logger.error(f"采集设备 {device.name} 性能数据失败: {result.get('message')}")
                    
            except Exception as e:
                failed_count += 1
                logger.exception(f"采集设备 {device.name} 性能数据时出现异常: {str(e)}")
        
        # 计算执行时间
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"设备性能数据采集完成。总计: {len(devices)}，成功: {success_count}，失败: {failed_count}，耗时: {duration:.2f}秒")

if __name__ == "__main__":
    # 当作为脚本运行时，直接执行数据采集
    from flask import Flask
    from src.db import init_db
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../../data/dev.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    init_db(app)
    
    with app.app_context():
        collect_performance_data() 