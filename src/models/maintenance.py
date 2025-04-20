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