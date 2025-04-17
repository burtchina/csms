#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备管理模块数据模型
"""

from datetime import datetime
from src.db import db

# 设备类型表
class DeviceType(db.Model):
    """设备类型模型"""
    __tablename__ = 'device_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联的设备
    devices = db.relationship('Device', backref='type', lazy='dynamic')
    
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
    
    def __repr__(self):
        return f'<DeviceType {self.name}>'

# 设备表
class Device(db.Model):
    """设备模型"""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_code = db.Column(db.String(50), unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('device_types.id'))
    location = db.Column(db.String(100))
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))
    username = db.Column(db.String(50))  # 设备登录用户名
    password = db.Column(db.String(100))  # 设备登录密码
    status = db.Column(db.String(20), default='正常')
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    warranty_period = db.Column(db.Integer)  # 保修期(月)
    last_maintenance = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __init__(self, name, device_code, type_id=None, location=None, ip_address=None, 
                 mac_address=None, username=None, password=None, status='正常', 
                 manufacturer=None, model=None, serial_number=None, 
                 purchase_date=None, warranty_period=None, notes=None):
        self.name = name
        self.device_code = device_code
        self.type_id = type_id
        self.location = location
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.username = username
        self.password = password
        self.status = status
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.purchase_date = purchase_date
        self.warranty_period = warranty_period
        self.notes = notes
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'device_code': self.device_code,
            'type_id': self.type_id,
            'type_name': self.type.name if self.type else None,
            'location': self.location,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'username': self.username,
            'password': '******' if self.password else None,  # 不返回明文密码
            'status': self.status,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'warranty_period': self.warranty_period,
            'last_maintenance': self.last_maintenance.strftime('%Y-%m-%d %H:%M') if self.last_maintenance else None,
            'next_maintenance': self.next_maintenance.strftime('%Y-%m-%d %H:%M') if self.next_maintenance else None,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Device {self.name}>' 