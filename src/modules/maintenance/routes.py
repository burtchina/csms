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
from src.models.maintenance import MaintenanceRecord, InspectionReport, InspectionItem
from src.modules.maintenance.inspection_service import batch_info_collect

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

# 设备巡检报告列表页面
@maintenance_bp.route('/inspection')
@login_required
def inspection_reports():
    # 预处理用户名，避免在模板中使用hasattr
    username = '系统'
    if current_user.is_authenticated:
        try:
            username = current_user.username
        except (AttributeError, TypeError):
            pass
    
    return render_template('maintenance/inspection_reports.html', operator_name=username)

# API：启动网络设备批量信息巡检
@maintenance_bp.route('/api/inspection/start', methods=['POST'])
@login_required
def start_batch_inspection():
    try:
        data = request.json or {}
        max_workers = data.get('max_workers', 5)
        
        # 避免使用hasattr
        operator = data.get('operator')
        if not operator:
            try:
                operator = current_user.username
            except (AttributeError, TypeError):
                operator = '系统'
        
        # 启动批量巡检（异步方式）
        # 注意：在实际生产环境中，应该使用 Celery 或其他任务队列来处理这种耗时操作
        # 这里为了简单，直接在请求中执行
        report_id = batch_info_collect(max_workers=max_workers, operator=operator)
        
        if report_id:
            return jsonify({
                'success': True,
                'message': '网络设备批量巡检已启动',
                'report_id': report_id
            })
        else:
            return jsonify({
                'success': False,
                'message': '启动网络设备批量巡检失败，详情请查看日志'
            }), 500
    
    except Exception as e:
        logger.error(f"启动网络设备批量巡检失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'启动巡检任务失败: {str(e)}'
        }), 500

# API：获取巡检报告列表
@maintenance_bp.route('/api/inspection/reports')
@login_required
def get_inspection_reports():
    try:
        reports = InspectionReport.query.order_by(InspectionReport.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [report.to_dict() for report in reports]
        })
    
    except Exception as e:
        logger.error(f"获取巡检报告列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取巡检报告列表失败: {str(e)}'
        }), 500

# API：获取单个巡检报告详情
@maintenance_bp.route('/api/inspection/reports/<int:report_id>')
@login_required
def get_inspection_report(report_id):
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({
                'success': False,
                'message': '巡检报告不存在'
            }), 404
        
        # 获取报告中的所有巡检项
        items = InspectionItem.query.filter_by(report_id=report_id).all()
        
        # 构造响应数据
        response = {
            'success': True,
            'data': {
                'report': report.to_dict(),
                'items': [item.to_dict() for item in items]
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"获取巡检报告 {report_id} 详情失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取巡检报告详情失败: {str(e)}'
        }), 500

# API：删除巡检报告
@maintenance_bp.route('/api/inspection/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_inspection_report(report_id):
    try:
        report = InspectionReport.query.get(report_id)
        if not report:
            return jsonify({
                'success': False,
                'message': '巡检报告不存在'
            }), 404
        
        # 删除报告（级联删除所有巡检项）
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '巡检报告已删除'
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'数据库错误: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"删除巡检报告 {report_id} 失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除巡检报告失败: {str(e)}'
        }), 500

# API：获取设备的巡检历史
@maintenance_bp.route('/api/inspection/device/<int:device_id>')
@login_required
def get_device_inspection_history(device_id):
    try:
        # 检查设备是否存在
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'message': '设备不存在'
            }), 404
        
        # 获取设备的所有巡检项
        items = InspectionItem.query.filter_by(device_id=device_id).order_by(InspectionItem.created_at.desc()).all()
        
        # 获取相关的报告ID
        report_ids = [item.report_id for item in items]
        reports = InspectionReport.query.filter(InspectionReport.id.in_(report_ids)).all()
        reports_dict = {report.id: report for report in reports}
        
        # 构造响应数据
        result = []
        for item in items:
            report = reports_dict.get(item.report_id)
            if report:
                result.append({
                    'inspection_item': item.to_dict(),
                    'report_title': report.title,
                    'report_date': report.start_time.isoformat() if report.start_time else None
                })
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        logger.error(f"获取设备 {device_id} 巡检历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取设备巡检历史失败: {str(e)}'
        }), 500 