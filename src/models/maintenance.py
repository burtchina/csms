#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
维护记录相关模型
"""

from datetime import datetime
from src.core.db import db
from src.models.base import BaseModel

class MaintenanceRecord(BaseModel):
    """维护记录模型"""
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    maintenance_type = db.Column(db.String(50), nullable=False)  # 维护类型：定期保养、故障维修、升级更新等
    maintenance_date = db.Column(db.Date, nullable=False)  # 维护日期
    maintenance_person = db.Column(db.String(50), nullable=False)  # 维护人员
    maintenance_content = db.Column(db.Text, nullable=False)  # 维护内容
    
    # 关联关系
    device = db.relationship('Device', backref='maintenance_records')
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id} for device {self.device_id}>'
    
    def to_dict(self):
        """转换为字典"""
        device_name = self.device.name if self.device else '未知设备'
        
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': device_name,
            'maintenance_type': self.maintenance_type,
            'maintenance_date': self.maintenance_date.isoformat() if self.maintenance_date else None,
            'maintenance_person': self.maintenance_person,
            'maintenance_content': self.maintenance_content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class InspectionReport(BaseModel):
    """设备巡检报告模型"""
    __tablename__ = 'inspection_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 巡检报告标题
    start_time = db.Column(db.DateTime, nullable=False)  # 巡检开始时间
    end_time = db.Column(db.DateTime, nullable=False)  # 巡检结束时间
    total_devices = db.Column(db.Integer, default=0)  # 巡检设备总数
    successful_devices = db.Column(db.Integer, default=0)  # 巡检成功设备数
    failed_devices = db.Column(db.Integer, default=0)  # 巡检失败设备数
    abnormal_devices = db.Column(db.Integer, default=0)  # 异常设备数
    summary = db.Column(db.Text)  # 巡检总结
    operator = db.Column(db.String(50))  # 操作人
    
    # 关联关系
    inspection_items = db.relationship('InspectionItem', backref='report', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InspectionReport {self.id} {self.title}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_devices': self.total_devices,
            'successful_devices': self.successful_devices,
            'failed_devices': self.failed_devices,
            'abnormal_devices': self.abnormal_devices,
            'summary': self.summary,
            'operator': self.operator,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class InspectionItem(BaseModel):
    """设备巡检项模型"""
    __tablename__ = 'inspection_items'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('inspection_reports.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    status = db.Column(db.String(20), default='正常')  # 巡检状态：正常、异常、失败
    cpu_usage = db.Column(db.Float)  # CPU使用率
    memory_usage = db.Column(db.Float)  # 内存使用率
    uptime = db.Column(db.String(100))  # 设备运行时间
    firmware_version = db.Column(db.String(50))  # 固件版本
    port_usage = db.Column(db.Text)  # 端口使用情况(JSON)
    system_load = db.Column(db.Float)  # 系统负载
    error_message = db.Column(db.Text)  # 错误信息
    inspection_results = db.Column(db.Text)  # 巡检结果详情(JSON)
    
    # 关联关系
    device = db.relationship('Device', backref='inspection_items')
    
    def __repr__(self):
        return f'<InspectionItem {self.id} for device {self.device_id}>'
    
    def to_dict(self):
        """转换为字典"""
        device_name = self.device.name if self.device else '未知设备'
        
        return {
            'id': self.id,
            'report_id': self.report_id,
            'device_id': self.device_id,
            'device_name': device_name,
            'device_ip': self.device.ip_address if self.device else None,
            'status': self.status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'uptime': self.uptime,
            'firmware_version': self.firmware_version,
            'port_usage': self.port_usage,
            'system_load': self.system_load,
            'error_message': self.error_message,
            'inspection_results': self.inspection_results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 