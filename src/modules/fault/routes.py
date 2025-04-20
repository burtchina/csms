#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
故障管理相关路由
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from src.core.db import db
from src.core.models import Fault, Alert, Device

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
fault_bp = Blueprint('fault', __name__)

# 故障列表页面
@fault_bp.route('/')
@login_required
def index():
    try:
        return render_template('fault/index.html')
    except Exception as e:
        logger.error(f"访问故障管理页面出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('errors/500.html', message=f"加载故障管理页面出错: {str(e)}")

# API：获取设备列表
@fault_bp.route('/api/devices')
@login_required
def get_devices():
    try:
        devices = Device.query.all()
        
        data = []
        for device in devices:
            device_data = {
                'id': device.id,
                'name': device.name,
                'type': str(device.type) if hasattr(device, 'type') else '',
                'status': device.status if hasattr(device, 'status') else ''
            }
            data.append(device_data)
        
        return jsonify({
            'status': 'success',
            'message': '获取设备列表成功',
            'data': data
        })
    
    except Exception as e:
        logger.error(f"获取设备列表出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'获取设备列表失败: {str(e)}'
        }), 500

# 设备API转发路由
@fault_bp.route('/devices/api/devices')
@login_required
def devices_api_proxy():
    # 转发到故障模块的设备列表API
    return get_devices()

# API：获取故障列表
@fault_bp.route('/api/faults')
@login_required
def get_faults():
    try:
        # 获取查询参数
        status = request.args.get('status')
        severity = request.args.get('severity')
        device_id = request.args.get('device_id')
        
        # 构建查询
        query = Fault.query
        
        # 应用过滤条件
        if status:
            query = query.filter(Fault.status == status)
        if severity:
            query = query.filter(Fault.severity == severity)
        if device_id:
            query = query.filter(Fault.device_id == device_id)
        
        # 执行查询
        faults = query.order_by(Fault.created_at.desc()).all()
        
        # 构建响应数据
        data = []
        for fault in faults:
            device = Device.query.get(fault.device_id)
            device_name = device.name if device else f"设备{fault.device_id}"
            
            fault_data = {
                'id': fault.id,
                'device_id': fault.device_id,
                'device_name': device_name,
                'fault_type': fault.fault_type,
                'severity': fault.severity,
                'description': fault.description,
                'status': fault.status,
                'created_at': fault.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': fault.updated_at.strftime('%Y-%m-%d %H:%M:%S') if fault.updated_at else None
            }
            data.append(fault_data)
        
        return jsonify({
            'status': 'success',
            'message': '获取故障列表成功',
            'data': data
        })
    
    except Exception as e:
        logger.error(f"获取故障列表出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'获取故障列表失败: {str(e)}'
        }), 500

# API：获取单个故障
@fault_bp.route('/api/faults/<int:fault_id>')
@login_required
def get_fault(fault_id):
    try:
        fault = Fault.query.get(fault_id)
        if not fault:
            return jsonify({
                'status': 'error',
                'message': '故障不存在'
            }), 404
        
        device = Device.query.get(fault.device_id)
        device_name = device.name if device else f"设备{fault.device_id}"
        
        fault_data = {
            'id': fault.id,
            'device_id': fault.device_id,
            'device_name': device_name,
            'fault_type': fault.fault_type,
            'severity': fault.severity,
            'description': fault.description,
            'status': fault.status,
            'created_at': fault.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': fault.updated_at.strftime('%Y-%m-%d %H:%M:%S') if fault.updated_at else None
        }
        
        return jsonify({
            'status': 'success',
            'message': '获取故障信息成功',
            'data': fault_data
        })
    
    except Exception as e:
        logger.error(f"获取故障 {fault_id} 信息出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取故障信息失败: {str(e)}'
        }), 500

# API：创建故障
@fault_bp.route('/api/faults', methods=['POST'])
@login_required
def create_fault():
    try:
        data = request.json
        
        # 验证必要字段
        required_fields = ['device_id', 'fault_type', 'severity', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        # 检查设备是否存在
        device = Device.query.get(data['device_id'])
        if not device:
            return jsonify({
                'status': 'error',
                'message': f'设备ID {data["device_id"]} 不存在'
            }), 400
        
        # 创建故障记录
        fault = Fault(
            device_id=data['device_id'],
            fault_type=data['fault_type'],
            severity=data['severity'],
            description=data['description'],
            status='open',
            reported_by=current_user.id
        )
        
        db.session.add(fault)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '故障记录创建成功',
            'data': {
                'id': fault.id
            }
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"创建故障记录出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'创建故障记录失败: {str(e)}'
        }), 500

# API：更新故障
@fault_bp.route('/api/faults/<int:fault_id>', methods=['PUT'])
@login_required
def update_fault(fault_id):
    try:
        fault = Fault.query.get(fault_id)
        if not fault:
            return jsonify({
                'status': 'error',
                'message': '故障不存在'
            }), 404
        
        data = request.json
        
        # 更新字段
        if 'fault_type' in data:
            fault.fault_type = data['fault_type']
        if 'severity' in data:
            fault.severity = data['severity']
        if 'description' in data:
            fault.description = data['description']
        if 'status' in data:
            fault.status = data['status']
        
        fault.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '故障记录更新成功',
            'data': {
                'id': fault.id
            }
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"更新故障记录出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'更新故障记录失败: {str(e)}'
        }), 500

# API：删除故障
@fault_bp.route('/api/faults/<int:fault_id>', methods=['DELETE'])
@login_required
def delete_fault(fault_id):
    try:
        fault = Fault.query.get(fault_id)
        if not fault:
            return jsonify({
                'status': 'error',
                'message': '故障不存在'
            }), 404
        
        db.session.delete(fault)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '故障记录删除成功'
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"删除故障记录出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'删除故障记录失败: {str(e)}'
        }), 500 