from datetime import datetime
from typing import Dict, Any, Optional

from src.core.db import db
from src.models import Device, PerformanceRecord

# 确保所有表都可以扩展
__table_args__ = {'extend_existing': True}

class PerformanceData(db.Model):
    """设备性能数据模型 - 保留以向后兼容"""
    __tablename__ = 'performance_data'
    __table_args__ = {'extend_existing': True}  # 确保可以扩展现有表
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    cpu_usage = db.Column(db.Float, nullable=True)
    memory_usage = db.Column(db.Float, nullable=True)
    uptime = db.Column(db.String(100), nullable=True)
    error = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PerformanceData device_id={self.device_id}, timestamp={self.timestamp}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'uptime': self.uptime,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }

def convert_to_performance_record(performance_data: PerformanceData) -> PerformanceRecord:
    """将PerformanceData转换为PerformanceRecord"""
    record = PerformanceRecord(
        device_id=performance_data.device_id,
        cpu_usage=performance_data.cpu_usage,
        memory_usage=performance_data.memory_usage,
        recorded_at=performance_data.timestamp
    )
    return record 

class Alert(db.Model):
    """设备告警记录模型"""
    __tablename__ = 'alerts'
    __table_args__ = {'extend_existing': True}  # 确保可以扩展现有表
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # cpu_usage, memory_usage, bandwidth_usage
    alert_level = db.Column(db.String(20), nullable=False)  # 信息, 警告, 严重
    message = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Float, nullable=False)  # 触发告警的值
    threshold = db.Column(db.Float, nullable=False)  # 阈值
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    acknowledged = db.Column(db.Boolean, nullable=False, default=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    
    device = db.relationship('Device', backref=db.backref('alerts', lazy=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """将对象转换为字典"""
        result = {
            'id': self.id,
            'device_id': self.device_id,
            'device_name': self.device.name if self.device else f"设备{self.device_id}",
            'alert_type': self.alert_type,
            'alert_level': self.alert_level,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'acknowledged': self.acknowledged
        }
        
        if self.acknowledged and self.acknowledged_at:
            result['acknowledged_at'] = self.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')
            
        return result

# 非持久化数据对象 - 用于临时数据存储
class PerformanceDataDTO:
    """性能数据传输对象 - 用于临时数据存储，不持久化"""
    
    def __init__(self, device_id, cpu_usage=0.0, memory_usage=0.0, 
                 bandwidth_usage=0.0, uptime='', data_source='manual'):
        self.device_id = device_id
        self.cpu_usage = cpu_usage
        self.memory_usage = memory_usage
        self.bandwidth_usage = bandwidth_usage
        self.uptime = uptime
        self.data_source = data_source
        self.timestamp = datetime.now()
    
    def to_dict(self):
        """将对象转换为字典"""
        return {
            'device_id': self.device_id,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'bandwidth_usage': self.bandwidth_usage,
            'uptime': self.uptime,
            'data_source': self.data_source,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } 