#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from src.core.db import db

class Policy(db.Model):
    """策略模型类"""
    __tablename__ = 'policy'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default='draft')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系 - 避免在模板中直接使用creator关系
    creator = relationship('User', backref='policies', lazy='select')
    deployments = relationship('PolicyDeployment', backref='policy', cascade='all, delete-orphan')
    audit_logs = relationship('PolicyAuditLog', backref='policy')
    alerts = relationship('PolicyAlert', backref='policy')
    
    def __repr__(self):
        return f"<Policy(id={self.id}, name='{self.name}', type='{self.type}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'config': self.config,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 