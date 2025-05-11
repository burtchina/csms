from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.core.db import db


class PolicyDeployment(db.Model):
    """策略部署模型类"""
    __tablename__ = 'policy_deployment'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    status = Column(String(16), nullable=False, default='pending')  # pending, success, failed
    deployed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deployed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    config_snapshot = Column(JSON)
    result = Column(Text)
    
    # 关系
    deployer = relationship('User', backref='deployments')
    device = relationship('Device', backref='policy_deployments')
    
    def __repr__(self):
        return f"<PolicyDeployment(id={self.id}, policy_id={self.policy_id}, status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'device_id': self.device_id,
            'status': self.status,
            'deployed_at': self.deployed_at.isoformat(),
            'deployed_by': self.deployed_by,
            'config_snapshot': self.config_snapshot,
            'result': self.result
        } 