#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - API接口模块
提供设备监控数据的API接口
"""

import time
import random
import threading
import queue
import logging
from flask import Blueprint, jsonify, request

# 配置日志
logger = logging.getLogger(__name__)

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 引入数据库模型
from src.models.device import Device
from src.core.db import db

# 存储性能数据的队列
performance_data = queue.Queue(maxsize=100)

# 存储最新数据的变量
latest_data = {
    "cpu": 0,
    "memory": 0,
    "uptime": "0天0小时0分钟",
    "timestamp": time.time(),
    "interfaces": {
        "GigabitEthernet0/0/1": {
            "status": "up",
            "input_rate": 0,
            "output_rate": 0
        },
        "GigabitEthernet0/0/2": {
            "status": "up",
            "input_rate": 0,
            "output_rate": 0
        },
        "GigabitEthernet0/0/3": {
            "status": "down",
            "input_rate": 0,
            "output_rate": 0
        }
    }
}

# 模拟数据收集
def generate_mock_data():
    """生成模拟监控数据"""
    global latest_data
    
    # 确保数据不停变化
    day = random.randint(1, 30)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    
    # 更新数据
    timestamp = time.time()
    data = {
        "cpu": random.randint(5, 95),  # CPU使用率 5%-95%
        "memory": random.randint(20, 85),  # 内存使用率 20%-85%
        "uptime": f"{day}天{hour}小时{minute}分钟",
        "timestamp": timestamp,
        "interfaces": {
            "GigabitEthernet0/0/1": {
                "status": "up",
                "input_rate": random.randint(100000, 10000000),  # 100Kbps-10Mbps
                "output_rate": random.randint(100000, 5000000)   # 100Kbps-5Mbps
            },
            "GigabitEthernet0/0/2": {
                "status": "up",
                "input_rate": random.randint(50000, 5000000),    # 50Kbps-5Mbps
                "output_rate": random.randint(50000, 2000000)    # 50Kbps-2Mbps
            },
            "GigabitEthernet0/0/3": {
                "status": random.choice(["up", "down"]),  # 随机状态
                "input_rate": random.randint(0, 1000000) if random.random() > 0.3 else 0,
                "output_rate": random.randint(0, 500000) if random.random() > 0.3 else 0
            }
        }
    }
    
    # 更新最新数据
    latest_data = data
    
    # 将数据放入队列
    if performance_data.full():
        performance_data.get()  # 移除最旧的数据
    performance_data.put(data)
    
    return data

# API路由
@api_bp.route('/data')
def get_data():
    """API端点：返回最新性能数据"""
    # 生成新的模拟数据
    generate_mock_data()
    return jsonify(latest_data)

@api_bp.route('/history')
def get_history():
    """API端点：返回历史性能数据"""
    # 确保有一些历史数据
    if performance_data.empty():
        for _ in range(5):
            generate_mock_data()
            time.sleep(0.1)  # 短暂延迟，避免数据完全相同
    
    # 获取队列中的所有数据
    history = list(performance_data.queue)
    return jsonify(history)

@api_bp.route('/devices')
def get_devices():
    """API端点：返回设备列表，供其他模块使用"""
    try:
        devices = Device.query.filter(Device.status != '报废').order_by(Device.name).all()
        return jsonify([
            {
                'id': device.id,
                'name': device.name,
                'device_code': device.device_code,
                'status': device.status
            } for device in devices
        ])
    except Exception as e:
        logger.error(f"获取设备列表时出错: {str(e)}")
        return jsonify([])

# 下面添加维护记录的API代理路由
@api_bp.route('/maintenance', methods=['GET'])
def get_maintenance_records():
    """API代理：获取所有维护记录"""
    from src.models.maintenance import MaintenanceRecord
    try:
        records = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).all()
        return jsonify([record.to_dict() for record in records])
    except Exception as e:
        logger.error(f"获取维护记录时出错: {str(e)}")
        return jsonify([])

@api_bp.route('/maintenance', methods=['POST'])
def create_maintenance_record():
    """API代理：创建新维护记录"""
    from datetime import datetime
    from src.models.maintenance import MaintenanceRecord
    try:
        data = request.json
        
        # 验证必填字段
        required_fields = ['device_id', 'maintenance_type', 'maintenance_date', 'maintenance_person', 'maintenance_content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 检查设备是否存在
        device = Device.query.get(data['device_id'])
        if not device:
            return jsonify({
                'success': False,
                'message': '设备不存在'
            }), 404
        
        # 处理日期
        try:
            maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': '日期格式不正确，请使用YYYY-MM-DD格式'
            }), 400
        
        # 创建维护记录
        record = MaintenanceRecord(
            device_id=data['device_id'],
            maintenance_type=data['maintenance_type'],
            maintenance_date=maintenance_date,
            maintenance_person=data['maintenance_person'],
            maintenance_content=data['maintenance_content']
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '维护记录已创建',
            'id': record.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建维护记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建维护记录失败: {str(e)}'
        }), 500

@api_bp.route('/maintenance/<int:record_id>', methods=['GET'])
def get_maintenance_record(record_id):
    """API代理：获取单个维护记录"""
    from src.models.maintenance import MaintenanceRecord
    try:
        record = MaintenanceRecord.query.get(record_id)
        if not record:
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        return jsonify(record.to_dict())
        
    except Exception as e:
        logger.error(f"获取维护记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取维护记录失败: {str(e)}'
        }), 500

@api_bp.route('/maintenance/<int:record_id>', methods=['DELETE'])
def delete_maintenance_record(record_id):
    """API代理：删除维护记录"""
    from src.models.maintenance import MaintenanceRecord
    try:
        record = MaintenanceRecord.query.get(record_id)
        if not record:
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '维护记录已删除'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除维护记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除维护记录失败: {str(e)}'
        }), 500 