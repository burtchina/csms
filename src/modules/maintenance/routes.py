#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
维护管理相关路由
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from src.core.db import db
from src.models.device import Device
from src.models.maintenance import MaintenanceRecord

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
maintenance_bp = Blueprint('maintenance', __name__)

# 维护记录列表页面
@maintenance_bp.route('/')
@login_required
def index():
    return render_template('maintenance/index.html')

# API：获取所有维护记录
@maintenance_bp.route('/api/maintenance')
def get_maintenance_records():
    try:
        records = MaintenanceRecord.query.order_by(MaintenanceRecord.maintenance_date.desc()).all()
        return jsonify([record.to_dict() for record in records])
    except Exception as e:
        logger.error(f"获取维护记录时出错: {str(e)}")
        return jsonify([])

# API：创建新维护记录
@maintenance_bp.route('/api/maintenance', methods=['POST'])
@login_required
def create_maintenance_record():
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
        
        # 更新设备状态为"正常"（如果是故障维修）
        if data['maintenance_type'] == '故障维修' and device.status == '维修中':
            device.status = '正常'
            db.session.commit()
            logger.info(f"设备 {device.name} 状态已更新为正常")
        
        return jsonify({
            'success': True,
            'message': '维护记录已创建',
            'id': record.id
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"创建维护记录时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理请求时出错: {str(e)}'
        }), 500

# API：获取单个维护记录
@maintenance_bp.route('/api/maintenance/<int:record_id>')
@login_required
def get_maintenance_record(record_id):
    try:
        record = MaintenanceRecord.query.get(record_id)
        if not record:
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': record.to_dict()
        })
    
    except Exception as e:
        logger.error(f"获取维护记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取维护记录失败: {str(e)}'
        }), 500

# API：删除维护记录
@maintenance_bp.route('/api/maintenance/<int:record_id>', methods=['DELETE'])
@login_required
def delete_maintenance_record(record_id):
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
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"删除维护记录 {record_id} 时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除维护记录失败: {str(e)}'
        }), 500 