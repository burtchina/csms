#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略数据访问层
提供策略相关数据的CRUD操作
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from src.core.db import db
from src.modules.policy.models.policy import Policy
from src.modules.policy.models.policy_template import PolicyTemplate
from src.modules.policy.models.policy_deployment import PolicyDeployment
from src.modules.policy.models.policy_audit_log import PolicyAuditLog
from src.modules.policy.models.policy_alert import PolicyAlert


class PolicyRepository:
    """策略数据访问层"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, policy_data: Dict[str, Any]) -> Policy:
        """创建策略
        
        Args:
            policy_data: 策略数据字典
            
        Returns:
            创建的策略实例
        """
        policy = Policy(**policy_data)
        self.session.add(policy)
        self.session.commit()
        self.session.refresh(policy)
        return policy
    
    def get_by_id(self, policy_id: int) -> Optional[Policy]:
        """根据ID获取策略
        
        Args:
            policy_id: 策略ID
            
        Returns:
            策略实例或None
        """
        return self.session.query(Policy).filter(Policy.id == policy_id).first()
    
    def get_all(self, filters: Dict[str, Any] = None) -> List[Policy]:
        """获取所有策略
        
        Args:
            filters: 过滤条件
            
        Returns:
            策略列表
        """
        query = self.session.query(Policy)
        
        if filters:
            if 'name' in filters:
                query = query.filter(Policy.name.like(f"%{filters['name']}%"))
            if 'type' in filters:
                query = query.filter(Policy.type == filters['type'])
            if 'status' in filters:
                query = query.filter(Policy.status == filters['status'])
            if 'status_not' in filters:
                query = query.filter(Policy.status != filters['status_not'])
            if 'created_by' in filters:
                query = query.filter(Policy.created_by == filters['created_by'])
        
        return query.all()
    
    def update(self, policy_id: int, policy_data: Dict[str, Any]) -> Optional[Policy]:
        """更新策略
        
        Args:
            policy_id: 策略ID
            policy_data: 策略数据
            
        Returns:
            更新后的策略实例或None
        """
        policy = self.get_by_id(policy_id)
        if not policy:
            return None
        
        for key, value in policy_data.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        self.session.commit()
        self.session.refresh(policy)
        return policy
    
    def delete(self, policy_id: int) -> bool:
        """删除策略
        
        Args:
            policy_id: 策略ID
            
        Returns:
            是否删除成功
        """
        policy = self.get_by_id(policy_id)
        if not policy:
            return False
        
        # 逻辑删除，将状态设为deleted
        policy.status = 'deleted'
        self.session.commit()
        return True
    
    def hard_delete(self, policy_id: int) -> bool:
        """物理删除策略
        
        Args:
            policy_id: 策略ID
            
        Returns:
            是否删除成功
        """
        policy = self.get_by_id(policy_id)
        if not policy:
            return False
        
        self.session.delete(policy)
        self.session.commit()
        return True


class PolicyTemplateRepository:
    """策略模板仓库类"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, data):
        """创建新模板"""
        template = PolicyTemplate(**data)
        self.session.add(template)
        self.session.commit()
        return template
    
    def update(self, template_id, data):
        """更新模板"""
        template = self.get(template_id)
        if not template:
            return None
        
        # 系统预设模板不允许修改
        if template.is_system:
            return None
        
        for key, value in data.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self.session.commit()
        return template
    
    def delete(self, template_id):
        """删除模板"""
        template = self.get(template_id)
        if not template or template.is_system:
            return False
        
        self.session.delete(template)
        self.session.commit()
        return True
    
    def get(self, template_id):
        """获取单个模板"""
        return self.session.query(PolicyTemplate).filter(PolicyTemplate.id == template_id).first()
    
    def get_all(self, filters=None):
        """获取模板列表"""
        query = self.session.query(PolicyTemplate)
        
        if filters:
            if 'type' in filters:
                query = query.filter(PolicyTemplate.type == filters['type'])
            if 'is_system' in filters:
                query = query.filter(PolicyTemplate.is_system == filters['is_system'])
        
        return query.order_by(PolicyTemplate.name).all()


class PolicyDeploymentRepository:
    """策略部署仓库类"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, data):
        """创建新部署记录"""
        deployment = PolicyDeployment(**data)
        self.session.add(deployment)
        self.session.commit()
        return deployment
    
    def update(self, deployment_id, data):
        """更新部署记录"""
        deployment = self.get(deployment_id)
        if not deployment:
            return None
        
        for key, value in data.items():
            if hasattr(deployment, key):
                setattr(deployment, key, value)
        
        self.session.commit()
        return deployment
    
    def get(self, deployment_id):
        """获取单个部署记录"""
        return self.session.query(PolicyDeployment).filter(PolicyDeployment.id == deployment_id).first()
    
    def get_all(self, filters=None):
        """获取部署列表"""
        query = self.session.query(PolicyDeployment)
        
        if filters:
            if 'policy_id' in filters:
                query = query.filter(PolicyDeployment.policy_id == filters['policy_id'])
            if 'device_id' in filters:
                query = query.filter(PolicyDeployment.device_id == filters['device_id'])
            if 'status' in filters:
                query = query.filter(PolicyDeployment.status == filters['status'])
        
        return query.order_by(PolicyDeployment.deployed_at.desc()).all()
    
    def get_latest_deployment(self, policy_id, device_id):
        """获取最新的部署记录"""
        return self.session.query(PolicyDeployment).filter(
            PolicyDeployment.policy_id == policy_id, 
            PolicyDeployment.device_id == device_id
        ).order_by(PolicyDeployment.deployed_at.desc()).first()


class PolicyAuditLogRepository:
    """策略审计日志仓库类"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, data):
        """创建审计日志"""
        log = PolicyAuditLog(**data)
        self.session.add(log)
        self.session.commit()
        return log
    
    def get(self, log_id):
        """获取单个日志"""
        return self.session.query(PolicyAuditLog).filter(PolicyAuditLog.id == log_id).first()
    
    def get_all(self, filters=None, page=1, per_page=20):
        """获取日志列表，支持分页"""
        query = self.session.query(PolicyAuditLog)
        
        if filters:
            if 'policy_id' in filters:
                query = query.filter(PolicyAuditLog.policy_id == filters['policy_id'])
            if 'user_id' in filters:
                query = query.filter(PolicyAuditLog.user_id == filters['user_id'])
            if 'action' in filters:
                query = query.filter(PolicyAuditLog.action == filters['action'])
            if 'start_date' in filters:
                query = query.filter(PolicyAuditLog.created_at >= filters['start_date'])
            if 'end_date' in filters:
                query = query.filter(PolicyAuditLog.created_at <= filters['end_date'])
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        logs = query.order_by(PolicyAuditLog.created_at.desc()) \
                   .offset((page - 1) * per_page) \
                   .limit(per_page) \
                   .all()
        
        return logs, total


class PolicyAlertRepository:
    """策略告警仓库类"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, data):
        """创建告警"""
        alert = PolicyAlert(**data)
        self.session.add(alert)
        self.session.commit()
        return alert
    
    def update(self, alert_id, data):
        """更新告警"""
        alert = self.get(alert_id)
        if not alert:
            return None
        
        for key, value in data.items():
            if hasattr(alert, key):
                setattr(alert, key, value)
        
        self.session.commit()
        return alert
    
    def acknowledge_alert(self, alert_id, user_id):
        """确认告警"""
        from datetime import datetime
        
        alert = self.get(alert_id)
        if not alert or alert.status != 'new':
            return False
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()
        self.session.commit()
        return True
    
    def resolve_alert(self, alert_id):
        """解决告警"""
        alert = self.get(alert_id)
        if not alert or alert.status == 'resolved':
            return False
        
        alert.status = 'resolved'
        self.session.commit()
        return True
    
    def get(self, alert_id):
        """获取单个告警"""
        return self.session.query(PolicyAlert).filter(PolicyAlert.id == alert_id).first()
    
    def get_all(self, filters=None, page=1, per_page=20):
        """获取告警列表，支持分页"""
        query = self.session.query(PolicyAlert)
        
        if filters:
            if 'policy_id' in filters:
                query = query.filter(PolicyAlert.policy_id == filters['policy_id'])
            if 'device_id' in filters:
                query = query.filter(PolicyAlert.device_id == filters['device_id'])
            if 'status' in filters:
                query = query.filter(PolicyAlert.status == filters['status'])
            if 'severity' in filters:
                query = query.filter(PolicyAlert.severity == filters['severity'])
            if 'alert_type' in filters:
                query = query.filter(PolicyAlert.alert_type == filters['alert_type'])
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        alerts = query.order_by(PolicyAlert.created_at.desc()) \
                     .offset((page - 1) * per_page) \
                     .limit(per_page) \
                     .all()
        
        return alerts, total 