from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.core.db import db


class PolicyAuditLog(db.Model):
    """策略审计日志模型类"""
    __tablename__ = 'policy_audit_log'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(32), nullable=False)  # create, update, delete, deploy, rollback
    details = Column(Text)
    ip_address = Column(String(64))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    user = relationship('User', backref='policy_audit_logs')
    
    def __repr__(self):
        return f"<PolicyAuditLog(id={self.id}, policy_id={self.policy_id}, action='{self.action}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        } 