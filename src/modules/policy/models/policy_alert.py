from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.core.db import db


class PolicyAlert(db.Model):
    """策略告警模型类"""
    __tablename__ = 'policy_alert'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'))
    device_id = Column(Integer, ForeignKey('devices.id'))
    alert_type = Column(String(32), nullable=False)  # policy_violation, sync_failed 等
    severity = Column(String(16), nullable=False, default='warning')  # info, warning, critical
    details = Column(Text)
    status = Column(String(16), nullable=False, default='new')  # new, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    acknowledger = relationship('User', backref='acknowledged_alerts')
    device = relationship('Device', backref='policy_alerts')
    
    def __repr__(self):
        return f"<PolicyAlert(id={self.id}, policy_id={self.policy_id}, alert_type='{self.alert_type}', status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'device_id': self.device_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'details': self.details,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 