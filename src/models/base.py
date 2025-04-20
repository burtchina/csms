#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础模型
为所有模型提供共享属性
"""

from datetime import datetime
from src.core.db import db

class BaseModel(db.Model):
    __table_args__ = {'extend_existing': True}
    """基础模型类，提供共享属性"""
    __abstract__ = True  # 标记为抽象类，不会创建数据库表
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """保存模型实例到数据库"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"保存数据失败: {str(e)}")
            return False
            
    def delete(self):
        """从数据库删除模型实例"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"删除数据失败: {str(e)}")
            return False
    
    @classmethod
    def get_by_id(cls, id):
        """根据ID获取实例"""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """获取所有实例"""
        return cls.query.all() 