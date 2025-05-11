from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from src.core.db import db


class PolicyTemplate(db.Model):
    """策略模板模型类"""
    __tablename__ = 'policy_template'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    is_system = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    creator = relationship('User', backref='templates')
    
    def __repr__(self):
        return f"<PolicyTemplate(id={self.id}, name='{self.name}', type='{self.type}')>" 