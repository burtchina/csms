#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能记录相关模型
"""

from datetime import datetime
from src.core.db import db
from src.models.base import BaseModel
from src.models.device import Device

class PerformanceRecord(BaseModel):
    """性能记录模型"""
    __tablename__ = 'performance_records'
    __table_args__ = {'extend_existing': True}  # 添加此参数解决表重复定义问题
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    cpu_usage = db.Column(db.Float, nullable=True)
    memory_usage = db.Column(db.Float, nullable=True)
    bandwidth_usage = db.Column(db.Float, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    
    # 关联设备 - 注意反向关联名称要与core/models.py中一致
    device = db.relationship('Device', backref=db.backref('performance_records', lazy='dynamic'), overlaps="performance_records")
    
    def __repr__(self):
        return f'<PerformanceRecord {self.id} (Device: {self.device_id})>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'bandwidth_usage': self.bandwidth_usage,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Threshold(BaseModel):
    """阈值模型"""
    __tablename__ = 'thresholds'
    __table_args__ = {'extend_existing': True}  # 添加此参数解决表重复定义问题
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    metric_name = db.Column(db.String(32), nullable=False)
    warning_threshold = db.Column(db.Float, nullable=False)
    critical_threshold = db.Column(db.Float, nullable=False)
    
    # 关联设备 - 注意反向关联名称要与core/models.py中一致
    device = db.relationship('Device', backref=db.backref('thresholds', lazy='dynamic'), overlaps="thresholds")
    
    def __repr__(self):
        return f'<Threshold {self.metric_name} (Device: {self.device_id})>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else None,
            'metric_name': self.metric_name,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 