#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能监控视图模块
"""

from flask import Blueprint, render_template, jsonify, abort, request, redirect, url_for
from flask_login import login_required
from datetime import datetime, timedelta
import random  # 用于生成模拟数据

from src.core.db import db
# 从统一位置导入所有模型
from src.models import Device, PerformanceRecord, Threshold
from src.modules.performance.models import PerformanceData, convert_to_performance_record

# 创建蓝图
performance_bp = Blueprint('performance', __name__, template_folder='templates')

# 性能监控首页
@performance_bp.route('/')
@login_required
def index():
    """性能监控首页"""
    return redirect(url_for('performance.dashboard'))

# 实时监控视图
@performance_bp.route('/realtime/<int:device_id>')
@login_required
def realtime_monitor(device_id):
    """渲染实时性能监控页面"""
    try:
        device = Device.query.get_or_404(device_id)
        
        # 导入collect_performance_data函数获取性能数据
        from src.modules.performance.services import collect_performance_data
        
        # 使用服务层函数获取初始性能数据
        initial_data = collect_performance_data(device_id)
        
        # 如果获取失败，使用模拟数据
        if not initial_data:
            current_time = datetime.now()
            uptime = "3天4小时27分钟"  # 实际应用中应从设备获取
            
            initial_data = {
                'cpu_usage': random.uniform(10, 90),
                'memory_usage': random.uniform(20, 80),
                'disk_usage': random.uniform(30, 70),
                'uptime': uptime,
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 使用原始的realtime.html模板，因为其功能正常
        return render_template('performance/realtime.html', device=device, initial_data=initial_data)
    except Exception as e:
        import logging
        logging.error(f"访问实时监控页面出错: {str(e)}")
        return render_template('error.html', message=f"加载实时监控出错: {str(e)}")

# 实时数据API
@performance_bp.route('/api/realtime/<int:device_id>')
@login_required
def get_realtime_data(device_id):
    """获取设备的实时性能数据"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': '设备不存在'}), 404
        
        # 在实际应用中，这里应该从性能监控系统获取数据
        # 这里使用模拟数据作为示例
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            'timestamp': current_time,
            'cpu_usage': random.uniform(10, 90),
            'memory_usage': random.uniform(20, 80),
            'disk_usage': random.uniform(30, 70),
            'network_in': random.uniform(0, 100),
            'network_out': random.uniform(0, 100)
        }
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        import logging
        logging.error(f"获取实时数据API出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 历史数据API
@performance_bp.route('/api/history/<int:device_id>')
@login_required
def get_history_data(device_id):
    """获取设备的历史性能数据"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': '设备不存在'}), 404
        
        # 获取时间范围参数，默认24小时
        hours = int(request.args.get('hours', 24))
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 查询历史性能数据
        records = PerformanceRecord.query.filter(
            PerformanceRecord.device_id == device_id,
            PerformanceRecord.recorded_at >= start_time,
            PerformanceRecord.recorded_at <= end_time
        ).order_by(PerformanceRecord.recorded_at).all()
        
        # 如果新模型没有数据，尝试从旧模型获取
        if not records:
            old_records = PerformanceData.query.filter(
                PerformanceData.device_id == device_id,
                PerformanceData.timestamp >= start_time,
                PerformanceData.timestamp <= end_time
            ).order_by(PerformanceData.timestamp).all()
            
            # 转换旧模型数据到新数据结构
            data_points = []
            for record in old_records:
                data_points.append({
                    'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_usage': record.cpu_usage or 0,
                    'memory_usage': record.memory_usage or 0,
                    'disk_usage': random.uniform(30, 70),  # 补充模拟数据
                    'network_in': random.uniform(0, 100),
                    'network_out': random.uniform(0, 100)
                })
        else:
            # 使用新模型数据
            data_points = []
            for record in records:
                data_points.append({
                    'timestamp': record.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_usage': record.cpu_usage or 0,
                    'memory_usage': record.memory_usage or 0,
                    'bandwidth_usage': record.bandwidth_usage or 0,
                    'disk_usage': random.uniform(30, 70),  # 补充模拟数据
                    'network_in': random.uniform(0, 100),
                    'network_out': random.uniform(0, 100)
                })
        
        # 如果没有任何数据，生成模拟数据
        if not data_points:
            current = start_time
            while current <= end_time:
                data_points.append({
                    'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_usage': random.uniform(10, 90),
                    'memory_usage': random.uniform(20, 80),
                    'disk_usage': random.uniform(30, 70),
                    'network_in': random.uniform(0, 100),
                    'network_out': random.uniform(0, 100)
                })
                current += timedelta(minutes=30)  # 每30分钟一个数据点
        
        return jsonify({'success': True, 'data': data_points})
    except Exception as e:
        import logging
        logging.error(f"获取历史数据API出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 性能监控仪表板
@performance_bp.route('/dashboard')
@login_required
def dashboard():
    """渲染性能监控仪表板"""
    try:
        # 导入SQLAlchemy inspect来检查表结构
        from sqlalchemy import inspect
        
        # 检查devices表中是否存在firmware_version列
        inspector = inspect(db.engine)
        device_columns = {col['name'] for col in inspector.get_columns('devices')}
        
        # 使用新模型结构，但仅包含存在的列
        devices = Device.query.with_entities(
            Device.id, 
            Device.name, 
            Device.ip_address, 
            Device.type_id, 
            Device.location, 
            Device.status
        ).all()
        
        # 转化为字典列表，这样在模板中使用时就不会尝试访问不存在的属性
        devices_list = []
        for device in devices:
            device_dict = {
                'id': device.id,
                'name': device.name,
                'ip_address': device.ip_address,
                'type_id': device.type_id,
                'location': device.location,
                'status': device.status
            }
            devices_list.append(device_dict)
            
        return render_template('performance/dashboard.html', devices=devices_list)
    except Exception as e:
        import logging
        logging.error(f"加载性能监控仪表板出错: {str(e)}")
        return render_template('error.html', message=f"加载仪表板出错: {str(e)}")

# 设备性能数据API
@performance_bp.route('/data/<int:device_id>')
@login_required
def get_data(device_id):
    """获取设备的性能数据"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': '设备不存在'}), 404
        
        # 尝试获取最新的性能记录
        record = PerformanceRecord.query.filter_by(device_id=device_id).order_by(PerformanceRecord.recorded_at.desc()).first()
        
        # 如果新模型没有数据，尝试从旧模型获取
        if not record:
            old_record = PerformanceData.query.filter_by(device_id=device_id).order_by(PerformanceData.timestamp.desc()).first()
            if old_record:
                # 这里我们可以选择将旧模型数据转换并保存到新模型
                record = convert_to_performance_record(old_record)
                try:
                    db.session.add(record)
                    db.session.commit()
                except Exception as conv_err:
                    db.session.rollback()
                    import logging
                    logging.error(f"转换旧性能数据失败: {str(conv_err)}")
        
        # 如果仍然没有数据，使用模拟数据
        if not record:
            current_time = datetime.now()
            uptime = "3天4小时27分钟"  # 实际应用中应从设备获取
            
            data = {
                'cpu_usage': random.uniform(10, 90),
                'memory_usage': random.uniform(20, 80),
                'disk_usage': random.uniform(30, 70),
                'uptime': uptime,
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            # 使用真实数据
            data = {
                'cpu_usage': record.cpu_usage or random.uniform(10, 90),
                'memory_usage': record.memory_usage or random.uniform(20, 80),
                'disk_usage': random.uniform(30, 70),
                'uptime': "数据来自数据库",
                'timestamp': record.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if record.recorded_at else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return jsonify(data)
    except Exception as e:
        import logging
        logging.error(f"获取设备性能数据出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# 新增一个专门用于实时监控页面的数据API
@performance_bp.route('/realtime_data/<int:device_id>')
@login_required
def get_realtime_page_data(device_id):
    """获取实时监控页面的性能数据（避免与routes.py中的路由冲突）"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'error': '设备不存在'}), 404
        
        # 这里我们返回一些模拟数据
        current_time = datetime.now()
        uptime = "3天4小时27分钟"  # 实际应用中应从设备获取
        
        data = {
            'cpu_usage': random.uniform(10, 90),
            'memory_usage': random.uniform(20, 80),
            'disk_usage': random.uniform(30, 70),
            'uptime': uptime,
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(data)
    except Exception as e:
        import logging
        logging.error(f"获取实时页面数据出错: {str(e)}")
        return jsonify({'error': str(e)}), 500 