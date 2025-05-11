#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略告警仓库
提供策略告警的数据访问功能
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from src.modules.policy.models.policy_alert import PolicyAlert
from src.modules.policy.models.policy import Policy
from src.models.device import Device


class PolicyAlertRepository:
    """策略告警仓库类，提供数据访问功能"""
    
    def __init__(self, session: Session):
        """初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def create(self, data: Dict[str, Any]) -> PolicyAlert:
        """创建告警
        
        Args:
            data: 告警数据
        
        Returns:
            PolicyAlert: 创建的告警对象
        """
        alert = PolicyAlert(**data)
        self.session.add(alert)
        self.session.commit()
        return alert
    
    def get(self, alert_id: int) -> Optional[PolicyAlert]:
        """获取单个告警
        
        Args:
            alert_id: 告警ID
        
        Returns:
            Optional[PolicyAlert]: 告警对象，如果不存在则返回None
        """
        return self.session.query(PolicyAlert).options(
            joinedload(PolicyAlert.policy),
            joinedload(PolicyAlert.device),
            joinedload(PolicyAlert.acknowledger)
        ).filter(PolicyAlert.id == alert_id).first()
    
    def get_all(self, filters: Dict[str, Any] = None) -> List[PolicyAlert]:
        """获取告警列表
        
        Args:
            filters: 过滤条件
                - status: 告警状态
                - severity: 严重程度
                - alert_type: 告警类型
                - policy_id: 策略ID
                - device_id: 设备ID
        
        Returns:
            List[PolicyAlert]: 告警列表
        """
        if filters is None:
            filters = {}
        
        query = self.session.query(PolicyAlert).options(
            joinedload(PolicyAlert.policy),
            joinedload(PolicyAlert.device),
            joinedload(PolicyAlert.acknowledger)
        )
        
        # 应用过滤条件
        if 'status' in filters and filters['status']:
            query = query.filter(PolicyAlert.status == filters['status'])
        
        if 'severity' in filters and filters['severity']:
            query = query.filter(PolicyAlert.severity == filters['severity'])
        
        if 'alert_type' in filters and filters['alert_type']:
            query = query.filter(PolicyAlert.alert_type == filters['alert_type'])
        
        if 'policy_id' in filters and filters['policy_id']:
            query = query.filter(PolicyAlert.policy_id == filters['policy_id'])
        
        if 'device_id' in filters and filters['device_id']:
            query = query.filter(PolicyAlert.device_id == filters['device_id'])
        
        # 按创建时间降序排序
        query = query.order_by(desc(PolicyAlert.created_at))
        
        return query.all()
    
    def update(self, alert_id: int, data: Dict[str, Any]) -> bool:
        """更新告警
        
        Args:
            alert_id: 告警ID
            data: 更新的数据
        
        Returns:
            bool: 是否成功更新
        """
        alert = self.get(alert_id)
        if not alert:
            return False
        
        for key, value in data.items():
            setattr(alert, key, value)
        
        self.session.commit()
        return True
    
    def delete(self, alert_id: int) -> bool:
        """删除告警
        
        Args:
            alert_id: 告警ID
        
        Returns:
            bool: 是否成功删除
        """
        alert = self.get(alert_id)
        if not alert:
            return False
        
        self.session.delete(alert)
        self.session.commit()
        return True 