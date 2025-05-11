#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略告警服务
提供策略告警的业务逻辑处理
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.core.db import db
from src.modules.policy.models.policy_alert import PolicyAlert
from src.modules.policy.repositories.policy_alert_repository import PolicyAlertRepository


class PolicyAlertService:
    """策略告警服务类，提供告警相关的业务逻辑处理"""
    
    def __init__(self):
        """初始化服务"""
        self.repo = PolicyAlertRepository(db.session)
        self.logger = logging.getLogger(__name__)
    
    def get_all_alerts(self, filters: Dict[str, Any] = None) -> List[PolicyAlert]:
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
        
        try:
            return self.repo.get_all(filters)
        except Exception as e:
            self.logger.error(f"获取告警列表失败: {str(e)}")
            return []
    
    def get_alert(self, alert_id: int) -> Optional[PolicyAlert]:
        """获取告警详情
        
        Args:
            alert_id: 告警ID
        
        Returns:
            Optional[PolicyAlert]: 告警对象，如果不存在则返回None
        """
        try:
            return self.repo.get(alert_id)
        except Exception as e:
            self.logger.error(f"获取告警详情失败: {str(e)}")
            return None
    
    def create_alert(self, data: Dict[str, Any]) -> Tuple[bool, Optional[int], str]:
        """创建告警
        
        Args:
            data: 告警数据
                - policy_id: 策略ID (可选)
                - device_id: 设备ID (可选)
                - alert_type: 告警类型
                - severity: 严重程度
                - details: 详细信息
        
        Returns:
            Tuple[bool, Optional[int], str]: (是否成功, 告警ID, 错误信息)
        """
        try:
            # 设置默认值
            if 'status' not in data:
                data['status'] = 'new'
            
            # 创建告警
            alert = self.repo.create(data)
            
            return True, alert.id, ""
        except Exception as e:
            self.logger.error(f"创建告警失败: {str(e)}")
            db.session.rollback()
            return False, None, str(e)
    
    def update_alert_status(self, alert_id: int, status: str, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """更新告警状态
        
        Args:
            alert_id: 告警ID
            status: 新状态 (new/acknowledged/resolved)
            user_id: 操作用户ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 获取告警
            alert = self.get_alert(alert_id)
            if not alert:
                return False, "告警不存在"
            
            # 状态验证
            if status not in ['new', 'acknowledged', 'resolved']:
                return False, f"无效的状态: {status}"
            
            # 验证状态流转
            if status == 'new' and alert.status != 'new':
                return False, "已确认或已解决的告警不能重置为新建状态"
            
            if status == 'acknowledged' and alert.status == 'resolved':
                return False, "已解决的告警不能设置为已确认状态"
            
            # 更新状态
            update_data = {
                'status': status,
                'updated_at': datetime.now()
            }
            
            # 如果是确认状态，记录确认人
            if status == 'acknowledged':
                update_data['acknowledged_by'] = user_id
                update_data['acknowledged_at'] = datetime.now()
            
            self.repo.update(alert_id, update_data)
            
            return True, ""
        except Exception as e:
            self.logger.error(f"更新告警状态失败: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> Tuple[bool, str]:
        """确认告警
        
        Args:
            alert_id: 告警ID
            user_id: 确认用户ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        return self.update_alert_status(alert_id, 'acknowledged', user_id)
    
    def resolve_alert(self, alert_id: int, user_id: int) -> Tuple[bool, str]:
        """解决告警
        
        Args:
            alert_id: 告警ID
            user_id: 操作用户ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        return self.update_alert_status(alert_id, 'resolved', user_id)
    
    def delete_alert(self, alert_id: int) -> Tuple[bool, str]:
        """删除告警
        
        Args:
            alert_id: 告警ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 获取告警
            alert = self.get_alert(alert_id)
            if not alert:
                return False, "告警不存在"
            
            # 删除告警
            self.repo.delete(alert_id)
            
            return True, ""
        except Exception as e:
            self.logger.error(f"删除告警失败: {str(e)}")
            db.session.rollback()
            return False, str(e) 