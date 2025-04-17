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
from flask import Blueprint, jsonify

# 创建API蓝图
api_bp = Blueprint('api', __name__)

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