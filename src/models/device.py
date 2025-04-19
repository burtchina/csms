#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备相关模型
"""

from src.core.db import db
from src.models.base import BaseModel

class DeviceType(BaseModel):
    """设备类型模型"""
    __tablename__ = 'device_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    # 关联关系
    devices = db.relationship('Device', backref='type', lazy=True)
    
    def __repr__(self):
        return f'<DeviceType {self.name}>'

class Device(BaseModel):
    """设备模型"""
    __tablename__ = 'devices'
    __table_args__ = {'extend_existing': True}  # 确保可以扩展现有表
    
    # 基本字段 - 这些字段应该与现有数据库结构匹配
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(20), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('device_types.id'))
    location = db.Column(db.String(100))
    status = db.Column(db.String(20), default='正常')
    
    # 以下字段可能在现有数据库中不存在，使用nullable=True确保向前兼容
    # 在数据库迁移后这些字段会被添加
    serial_number = db.Column(db.String(50), nullable=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    device_code = db.Column(db.String(50), nullable=True, unique=True)
    mac_address = db.Column(db.String(20), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    warranty_period = db.Column(db.Integer, nullable=True)  # 保修期（月）
    notes = db.Column(db.Text, nullable=True)
    
    # SSH连接信息
    username = db.Column(db.String(50), default='admin', nullable=True)
    password = db.Column(db.String(100), default='admin123', nullable=True)
    port = db.Column(db.Integer, default=22, nullable=True)
    connection_protocol = db.Column(db.String(20), default='ssh', nullable=True)  # ssh, telnet, snmp
    
    def __repr__(self):
        return f'<Device {self.name} ({self.ip_address})>'
    
    def to_dict(self):
        """转换为字典"""
        type_name = self.type.name if self.type else None
        
        # 基本信息字典
        result = {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'type_id': self.type_id,
            'type_name': type_name,
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 追加可能不存在的字段（如果存在）
        if hasattr(self, 'device_code') and self.device_code:
            result['device_code'] = self.device_code
        
        if hasattr(self, 'serial_number') and self.serial_number:
            result['serial_number'] = self.serial_number
            
        if hasattr(self, 'firmware_version') and self.firmware_version:
            result['firmware_version'] = self.firmware_version
            
        if hasattr(self, 'mac_address') and self.mac_address:
            result['mac_address'] = self.mac_address
            
        if hasattr(self, 'manufacturer') and self.manufacturer:
            result['manufacturer'] = self.manufacturer
            
        if hasattr(self, 'model') and self.model:
            result['model'] = self.model
            
        if hasattr(self, 'purchase_date') and self.purchase_date:
            result['purchase_date'] = self.purchase_date.isoformat()
            
        if hasattr(self, 'warranty_period') and self.warranty_period:
            result['warranty_period'] = self.warranty_period
            
        if hasattr(self, 'connection_protocol') and self.connection_protocol:
            result['connection_protocol'] = self.connection_protocol
            
        return result

# 初始化基本设备类型
def init_device_types():
    """初始化设备类型数据"""
    try:
        # 检查是否已有数据
        if DeviceType.query.count() > 0:
            return True
            
        # 添加常见设备类型
        device_types = [
            {"name": "路由器", "description": "网络路由设备"},
            {"name": "交换机", "description": "网络交换设备"},
            {"name": "服务器", "description": "物理或虚拟服务器"},
            {"name": "防火墙", "description": "网络安全设备"},
            {"name": "存储设备", "description": "数据存储设备"},
            {"name": "无线AP", "description": "无线接入点"},
            {"name": "负载均衡器", "description": "流量负载均衡设备"}
        ]
        
        for type_data in device_types:
            device_type = DeviceType(name=type_data["name"], description=type_data["description"])
            db.session.add(device_type)
            
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        import logging
        logging.error(f"初始化设备类型失败: {str(e)}")
        return False 