#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 核心数据库模型
注意: 设备相关模型已移至src/models/device.py
      性能相关模型已移至src/models/performance.py
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json

from src.core.db import db, login_manager
# 导入新位置的模型
from src.models.device import Device
from src.models.performance import PerformanceRecord, Threshold

# 用户模型
class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    role = db.relationship('Role', backref='users')
    
    @property
    def password(self):
        """密码不可读取"""
        raise AttributeError('密码不可读取')
    
    @password.setter
    def password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# 角色模型
class Role(db.Model):
    __table_args__ = {'extend_existing': True}
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    permissions = db.Column(db.Text)  # JSON格式存储权限
    description = db.Column(db.String(255))
    
    def set_permissions(self, permissions):
        """设置权限"""
        self.permissions = json.dumps(permissions)
    
    def get_permissions(self):
        """获取权限"""
        return json.loads(self.permissions) if self.permissions else {}
    
    def has_permission(self, permission):
        """检查是否有权限"""
        permissions = self.get_permissions()
        return permission in permissions
    
    def __repr__(self):
        return f'<Role {self.name}>'


# 设备模型已移至 src/models/device.py
# 性能模型已移至 src/models/performance.py


# 接口模型
class Interface(db.Model):
    __table_args__ = {'extend_existing': True}
    """接口模型"""
    __tablename__ = 'interfaces'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32))
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))
    status = db.Column(db.String(16), default='unknown')  # up, down, error
    
    def __repr__(self):
        return f'<Interface {self.name} ({self.device.name})>'


# 故障模型
class Fault(db.Model):
    __table_args__ = {'extend_existing': True}
    """故障模型"""
    __tablename__ = 'faults'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    fault_type = db.Column(db.String(32), nullable=False)
    severity = db.Column(db.String(16), nullable=False)  # low, medium, high, critical
    description = db.Column(db.Text)
    status = db.Column(db.String(16), default='open')  # open, in_progress, resolved
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    reporter = db.relationship('User', backref='reported_faults')
    
    def __repr__(self):
        return f'<Fault {self.id} ({self.device.name})>'


# 维护任务模型
class MaintenanceTask(db.Model):
    __table_args__ = {'extend_existing': True}
    """维护任务模型"""
    __tablename__ = 'maintenance_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    status = db.Column(db.String(16), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(16), default='medium')  # low, medium, high, urgent
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    assignee = db.relationship('User', backref='assigned_tasks')
    
    def __repr__(self):
        return f'<MaintenanceTask {self.title}>'


# 任务日志模型
class TaskLog(db.Model):
    __table_args__ = {'extend_existing': True}
    """任务日志模型"""
    __tablename__ = 'task_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('maintenance_tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    task = db.relationship('MaintenanceTask', backref='logs')
    user = db.relationship('User', backref='task_logs')
    
    def __repr__(self):
        return f'<TaskLog {self.id}>'


# 性能记录模型已移至 src/models/performance.py
# from src.models.performance import PerformanceRecord


# 阈值模型已移至 src/models/performance.py
# from src.models.performance import Threshold


# 告警模型
class Alert(db.Model):
    __table_args__ = {'extend_existing': True}
    """告警模型"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    fault_id = db.Column(db.Integer, db.ForeignKey('faults.id'))
    alert_type = db.Column(db.String(32), nullable=False)
    severity = db.Column(db.String(16), nullable=False)  # low, medium, high, critical
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), default='active')  # active, acknowledged, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    fault = db.relationship('Fault', backref='alerts')
    
    def __repr__(self):
        return f'<Alert {self.id}>'


# 系统日志模型
class SystemLog(db.Model):
    __table_args__ = {'extend_existing': True}
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(32), nullable=False)
    target = db.Column(db.String(64))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='system_logs')
    
    def __repr__(self):
        return f'<SystemLog {self.id}>' 