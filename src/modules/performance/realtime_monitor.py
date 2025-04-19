#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
实时监控调试模块 - 使用模拟数据进行接口测试
"""

import random
import time
import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
realtime_debug_bp = Blueprint('realtime_debug', __name__)

# 导入性能监控相关服务
from src.modules.performance.services import RealTimeMonitor

# 测试数据生成函数
def generate_test_data(device_id):
    """生成测试数据"""
    return {
        'status': 'success',
        'data': {
            'cpu_usage': round(random.uniform(30, 90), 1),
            'memory_usage': round(random.uniform(40, 80), 1),
            'bandwidth_usage': round(random.uniform(20, 70), 1),
            'uptime': f"{random.randint(1,30)}天{random.randint(1,23)}小时{random.randint(1,59)}分钟",
            'timestamp': time.time(),
            'test_mode': True
        },
        'device_name': f"测试设备_{device_id}"
    }

# 测试接口
@realtime_debug_bp.route('/debug/data/<int:device_id>')
@login_required
def get_debug_data(device_id):
    """调试接口 - 获取模拟的实时数据"""
    logger.info(f"调试接口: 请求设备 {device_id} 的测试数据")
    return jsonify(generate_test_data(device_id))

# 健康检查接口
@realtime_debug_bp.route('/debug/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'success',
        'message': '调试接口正常工作中',
        'timestamp': time.time()
    })

# 添加新的API端点，直接返回带有固定值的数据
@realtime_debug_bp.route('/direct-data/<int:device_id>')
def get_direct_data(device_id):
    """调试API - 返回设备的真实性能数据"""
    logger.info(f"调试API: 请求设备 {device_id} 的实时数据")
    
    try:
        # 尝试从RealTimeMonitor获取真实数据
        result = RealTimeMonitor.get_latest_data(device_id)
        
        # 检查是否成功获取到数据
        if result.get('status') == 'success' and 'data' in result:
            logger.info(f"成功获取设备 {device_id} 的真实数据: CPU={result['data'].get('cpu_usage')}%, 内存={result['data'].get('memory_usage')}%")
            return jsonify(result)
        else:
            logger.warning(f"未能从RealTimeMonitor获取数据，使用模拟数据")
    except Exception as e:
        logger.error(f"获取真实数据时出错: {str(e)}")
    
    # 如果获取真实数据失败，返回模拟数据
    direct_data = {
        'status': 'success',
        'data': {
            'cpu_usage': round(random.uniform(30, 80), 1),
            'memory_usage': round(random.uniform(40, 85), 1),
            'bandwidth_usage': round(random.uniform(20, 70), 1),
            'uptime': f"{random.randint(1,30)}天{random.randint(1,23)}小时{random.randint(1,59)}分钟",
            'timestamp': time.time(),
            'test_mode': True
        },
        'device_name': f"测试设备_{device_id}"
    }
    
    logger.info(f"返回模拟数据: CPU={direct_data['data']['cpu_usage']}%, 内存={direct_data['data']['memory_usage']}%")
    return jsonify(direct_data) 