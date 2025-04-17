#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能监控相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime, timedelta
import random  # 仅用于演示，实际应用中应替换为真实数据采集
import numpy as np  # 用于生成更真实的模拟数据

from src.db import db
from src.core.models import Device, PerformanceRecord, Threshold
from src.modules.performance.services import PerformanceAnalyzer, PerformanceCollector, RealTimeMonitor

# 创建蓝图
performance_bp = Blueprint('performance', __name__, template_folder='templates')

# 性能监控主页
@performance_bp.route('/')
@login_required
def index():
    devices = Device.query.all()
    return render_template('performance/index.html', devices=devices)

# 性能数据获取接口
@performance_bp.route('/data')
@login_required
def get_performance_data():
    device_id = request.args.get('device_id', type=int)
    time_range = request.args.get('time_range', '24', type=int)  # 默认24小时
    
    if not device_id:
        return jsonify({'status': 'error', 'message': '缺少设备ID参数'})
    
    # 检查设备是否存在
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'status': 'error', 'message': '设备不存在'})
    
    # 计算时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=time_range)
    
    # 查询指定时间范围内的性能记录
    records = PerformanceRecord.query.filter(
        PerformanceRecord.device_id == device_id,
        PerformanceRecord.recorded_at >= start_time,
        PerformanceRecord.recorded_at <= end_time
    ).order_by(PerformanceRecord.recorded_at).all()
    
    # 如果没有记录，生成一些模拟数据
    if not records:
        # 生成更真实的模拟数据
        timestamps = []
        
        # 生成时间点，每5分钟一个数据点
        interval_minutes = 5
        num_points = (time_range * 60) // interval_minutes
        
        # 基础趋势生成
        x = np.linspace(0, 1, num_points)
        
        # CPU使用率 - 通常会有波动和高峰期
        cpu_base = 30 + 20 * np.sin(x * 2 * np.pi)  # 基础正弦波模式
        cpu_noise = np.random.normal(0, 5, num_points)  # 随机波动
        cpu_day_pattern = 15 * np.sin(x * 4 * np.pi)  # 模拟一天中的使用模式
        cpu_usage = np.clip(cpu_base + cpu_noise + cpu_day_pattern, 5, 95).tolist()
        
        # 内存使用率 - 通常较为稳定，但会缓慢变化
        memory_base = 40 + 15 * np.sin(x * np.pi / 2)  # 缓慢变化的基础
        memory_noise = np.random.normal(0, 3, num_points)  # 较小的随机波动
        memory_usage = np.clip(memory_base + memory_noise, 20, 85).tolist()
        
        # 带宽使用率 - 会有突发和高峰
        bandwidth_base = 20 + 10 * np.sin(x * 3 * np.pi)  # 基础波动
        bandwidth_spikes = np.zeros(num_points)
        spike_indices = np.random.choice(num_points, size=int(num_points * 0.1), replace=False)
        bandwidth_spikes[spike_indices] = np.random.uniform(15, 40, size=len(spike_indices))
        bandwidth_noise = np.random.normal(0, 4, num_points)  # 随机波动
        bandwidth_usage = np.clip(bandwidth_base + bandwidth_spikes + bandwidth_noise, 2, 90).tolist()
        
        # 生成时间戳
        current_time = start_time
        for _ in range(num_points):
            timestamps.append(current_time.strftime('%Y-%m-%d %H:%M'))
            current_time += timedelta(minutes=interval_minutes)
        
        return jsonify({
            'status': 'success',
            'data': {
                'timestamps': timestamps,
                'cpu_usage': [round(val, 1) for val in cpu_usage],
                'memory_usage': [round(val, 1) for val in memory_usage],
                'bandwidth_usage': [round(val, 1) for val in bandwidth_usage]
            },
            'message': '使用模拟数据（无实际记录）'
        })
    
    # 处理实际记录数据
    timestamps = [record.recorded_at.strftime('%Y-%m-%d %H:%M') for record in records]
    cpu_usage = [record.cpu_usage for record in records]
    memory_usage = [record.memory_usage for record in records]
    bandwidth_usage = [record.bandwidth_usage for record in records]
    
    return jsonify({
        'status': 'success',
        'data': {
            'timestamps': timestamps,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'bandwidth_usage': bandwidth_usage
        }
    })

# 实时监控页面
@performance_bp.route('/realtime')
@login_required
def realtime_monitoring():
    devices = Device.query.all()
    return render_template('dashboard.html')

# 启动实时监控
@performance_bp.route('/realtime/start/<int:device_id>', methods=['POST'])
@login_required
def start_realtime_monitoring(device_id):
    result = RealTimeMonitor.start_device_monitoring(device_id)
    return jsonify(result)

# 停止实时监控
@performance_bp.route('/realtime/stop/<int:device_id>', methods=['POST'])
@login_required
def stop_realtime_monitoring(device_id):
    result = RealTimeMonitor.stop_device_monitoring(device_id)
    return jsonify(result)

# 获取实时监控数据
@performance_bp.route('/realtime/data/<int:device_id>')
@login_required
def get_realtime_data(device_id):
    return jsonify(RealTimeMonitor.get_latest_data(device_id))

# 获取实时监控历史数据
@performance_bp.route('/realtime/history/<int:device_id>')
@login_required
def get_realtime_history(device_id):
    return jsonify(RealTimeMonitor.get_history_data(device_id))

# 性能分析页面
@performance_bp.route('/analyze')
@login_required
def analyze():
    device_id = request.args.get('device_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    devices = Device.query.all()
    analysis_result = None
    
    if device_id:
        # 调用性能分析服务
        analysis_result = PerformanceAnalyzer.analyze_device_performance(device_id, days)
    
    return render_template(
        'performance/analysis.html',
        devices=devices,
        selected_device_id=device_id,
        days=days,
        analysis_result=analysis_result
    )

# 阈值管理页面
@performance_bp.route('/thresholds')
@login_required
def thresholds():
    devices = Device.query.all()
    thresholds = Threshold.query.all()
    return render_template('performance/thresholds.html', devices=devices, thresholds=thresholds)

# 添加阈值
@performance_bp.route('/thresholds/add', methods=['POST'])
@login_required
def add_threshold():
    device_id = request.form.get('device_id', type=int)
    metric_name = request.form.get('metric_name')
    warning_threshold = request.form.get('warning_threshold', type=float)
    critical_threshold = request.form.get('critical_threshold', type=float)
    
    # 验证参数
    if not device_id or not metric_name or warning_threshold is None or critical_threshold is None:
        flash('缺少必要参数', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 检查设备是否存在
    device = Device.query.get(device_id)
    if not device:
        flash('设备不存在', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 检查阈值合理性
    if warning_threshold >= critical_threshold:
        flash('警告阈值必须小于严重阈值', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 检查是否已存在相同设备和指标的阈值
    existing = Threshold.query.filter_by(device_id=device_id, metric_name=metric_name).first()
    if existing:
        flash('该设备的指定指标已存在阈值设置，请编辑现有阈值', 'warning')
        return redirect(url_for('performance.thresholds'))
    
    # 创建新阈值
    new_threshold = Threshold(
        device_id=device_id,
        metric_name=metric_name,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold
    )
    
    try:
        db.session.add(new_threshold)
        db.session.commit()
        flash('阈值设置成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'阈值设置失败: {str(e)}', 'danger')
    
    return redirect(url_for('performance.thresholds'))

# 更新阈值
@performance_bp.route('/thresholds/update', methods=['POST'])
@login_required
def update_threshold():
    threshold_id = request.form.get('threshold_id', type=int)
    device_id = request.form.get('device_id', type=int)
    metric_name = request.form.get('metric_name')
    warning_threshold = request.form.get('warning_threshold', type=float)
    critical_threshold = request.form.get('critical_threshold', type=float)
    
    # 验证参数
    if not threshold_id or not device_id or not metric_name or warning_threshold is None or critical_threshold is None:
        flash('缺少必要参数', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 检查阈值合理性
    if warning_threshold >= critical_threshold:
        flash('警告阈值必须小于严重阈值', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 获取要更新的阈值
    threshold = Threshold.query.get(threshold_id)
    if not threshold:
        flash('阈值不存在', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    # 检查是否尝试修改设备或指标，并且已存在相同设备和指标的其他阈值
    if (threshold.device_id != device_id or threshold.metric_name != metric_name):
        existing = Threshold.query.filter(
            Threshold.device_id == device_id,
            Threshold.metric_name == metric_name,
            Threshold.id != threshold_id
        ).first()
        if existing:
            flash('该设备的指定指标已存在阈值设置', 'danger')
            return redirect(url_for('performance.thresholds'))
    
    # 更新阈值
    threshold.device_id = device_id
    threshold.metric_name = metric_name
    threshold.warning_threshold = warning_threshold
    threshold.critical_threshold = critical_threshold
    
    try:
        db.session.commit()
        flash('阈值更新成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'阈值更新失败: {str(e)}', 'danger')
    
    return redirect(url_for('performance.thresholds'))

# 删除阈值
@performance_bp.route('/thresholds/delete', methods=['POST'])
@login_required
def delete_threshold():
    threshold_id = request.form.get('threshold_id', type=int)
    
    if not threshold_id:
        flash('缺少阈值ID参数', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    threshold = Threshold.query.get(threshold_id)
    if not threshold:
        flash('阈值不存在', 'danger')
        return redirect(url_for('performance.thresholds'))
    
    try:
        db.session.delete(threshold)
        db.session.commit()
        flash('阈值删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'阈值删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('performance.thresholds'))

# 手动触发性能数据采集
@performance_bp.route('/collect/<int:device_id>', methods=['POST'])
@login_required
def collect_device_data(device_id):
    try:
        # 调用性能数据采集服务
        result = PerformanceCollector.collect_device_performance(device_id)
        
        if result['status'] == 'success':
            flash('性能数据采集成功', 'success')
        else:
            flash(f'性能数据采集失败: {result.get("message", "未知错误")}', 'danger')
            
        # 重定向到性能监控页面
        return redirect(url_for('performance.index'))
    except Exception as e:
        flash(f'性能数据采集出错: {str(e)}', 'danger')
        return redirect(url_for('performance.index')) 