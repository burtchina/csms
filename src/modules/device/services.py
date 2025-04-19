#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备服务模块 - 提供设备相关功能
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.exc import SQLAlchemyError

from src.core.db import db
from src.models.device import Device, DeviceType
from src.modules.performance.ssh_monitor import (
    get_connection, 
    get_cpu_usage, 
    get_memory_usage, 
    get_uptime, 
    get_interface_stats,
    close_connection
)

# 设置日志
logger = logging.getLogger(__name__)

def get_device_by_id(device_id: int) -> Optional[Device]:
    """获取设备信息"""
    return Device.query.get(device_id)

def get_all_devices() -> List[Device]:
    """获取所有设备列表"""
    return Device.query.all()

def test_device_connection(device_id: int) -> Dict:
    """
    测试设备连接
    
    Args:
        device_id: 设备ID
        
    Returns:
        测试结果
    """
    device = get_device_by_id(device_id)
    if not device:
        return {
            'success': False,
            'message': f'设备ID {device_id} 不存在'
        }
    
    # 检查设备是否有IP地址
    if not device.ip_address:
        return {
            'success': False,
            'message': f'设备 {device.name} 没有配置IP地址'
        }
    
    try:
        # 尝试SSH连接
        connection = get_connection(
            device_id, 
            device.ip_address, 
            device.username or 'admin', 
            device.password or 'admin123',
            device.port or 22
        )
        
        if not connection:
            return {
                'success': False,
                'message': f'无法连接到设备 {device.name} ({device.ip_address})'
            }
        
        # 测试获取设备信息
        uptime = get_uptime(device_id, connection)
        
        # 关闭连接
        close_connection(device_id)
        
        return {
            'success': True,
            'message': f'成功连接到设备 {device.name}',
            'uptime': uptime
        }
    except Exception as e:
        logger.error(f"测试设备 {device_id} 连接时出错: {str(e)}")
        return {
            'success': False,
            'message': f'连接测试出错: {str(e)}'
        }

def get_device_info(device_id: int) -> Dict:
    """
    获取设备详细信息
    
    Args:
        device_id: 设备ID
        
    Returns:
        设备信息
    """
    device = get_device_by_id(device_id)
    if not device:
        return {
            'success': False,
            'message': f'设备ID {device_id} 不存在'
        }
    
    try:
        # 基本设备信息
        result = {
            'success': True,
            'device': device.to_dict()
        }
        
        # 如果设备可连接，尝试获取更多信息
        if device.ip_address and device.status == '正常':
            try:
                # 尝试SSH连接
                connection = get_connection(
                    device_id, 
                    device.ip_address, 
                    device.username or 'admin', 
                    device.password or 'admin123',
                    device.port or 22
                )
                
                if connection:
                    # 获取设备信息
                    result['connection_status'] = 'connected'
                    result['uptime'] = get_uptime(device_id, connection)
                    result['cpu_usage'] = get_cpu_usage(device_id, connection)
                    result['memory_usage'] = get_memory_usage(device_id, connection)
                    result['interfaces'] = get_interface_stats(device_id, connection)
                    
                    # 关闭连接
                    close_connection(device_id)
                else:
                    result['connection_status'] = 'failed'
            except Exception as e:
                logger.error(f"获取设备 {device_id} 详细信息时出错: {str(e)}")
                result['connection_status'] = 'error'
                result['connection_error'] = str(e)
        else:
            result['connection_status'] = 'unavailable'
        
        return result
    
    except Exception as e:
        logger.error(f"获取设备 {device_id} 信息时出错: {str(e)}")
        return {
            'success': False,
            'message': f'获取设备信息出错: {str(e)}'
        } 