from typing import Dict, List, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from src.modules.policy.repositories.policy_audit_log_repository import PolicyAuditLogRepository


class PolicyAuditService:
    """策略审计服务类，负责策略审计日志的记录和查询"""

    def __init__(self, session=None):
        """
        初始化策略审计服务
        
        Args:
            session: 数据库会话
        """
        self.audit_repo = PolicyAuditLogRepository(session)

    def add_audit_log(self, policy_id: int, user_id: int, action: str, details: str, ip_address: str = None) -> Tuple[bool, Any]:
        """
        添加审计日志
        
        Args:
            policy_id: 策略ID
            user_id: 用户ID
            action: 操作类型（create/update/delete/deploy/rollback等）
            details: 详细内容
            ip_address: 操作IP地址
            
        Returns:
            (bool, Any): 是否成功，结果或错误消息
        """
        try:
            log_data = {
                'policy_id': policy_id,
                'user_id': user_id,
                'action': action,
                'details': details,
                'ip_address': ip_address,
                'created_at': datetime.utcnow()
            }
            
            log = self.audit_repo.create(log_data)
            return True, log
        except Exception as e:
            return False, str(e)

    def get_logs_by_policy(self, policy_id: int, limit: int = 100) -> List[Any]:
        """
        获取指定策略的审计日志
        
        Args:
            policy_id: 策略ID
            limit: 最大返回记录数
            
        Returns:
            List[Any]: 审计日志列表
        """
        try:
            logs = self.audit_repo.get_logs_by_policy(policy_id, limit)
            return logs
        except Exception as e:
            print(f"获取策略审计日志时发生错误: {str(e)}")
            return []

    def get_logs_by_user(self, user_id: int, limit: int = 100) -> List[Any]:
        """
        获取指定用户的审计日志
        
        Args:
            user_id: 用户ID
            limit: 最大返回记录数
            
        Returns:
            List[Any]: 审计日志列表
        """
        try:
            logs = self.audit_repo.get_logs_by_user(user_id, limit)
            return logs
        except Exception as e:
            print(f"获取用户审计日志时发生错误: {str(e)}")
            return []

    def get_logs(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Any]:
        """
        获取审计日志
        
        Args:
            filters: 过滤条件
            limit: 最大返回记录数
            
        Returns:
            List[Any]: 审计日志列表
        """
        try:
            if filters is None:
                filters = {}
            logs = self.audit_repo.get_all(filters, limit=limit)
            return logs
        except Exception as e:
            print(f"获取审计日志时发生错误: {str(e)}")
            return []

    def export_logs(self, filters: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """
        导出审计日志
        
        Args:
            filters: 过滤条件
            
        Returns:
            (bool, Any): 是否成功，结果或错误消息
        """
        # 实现导出逻辑，可以导出为CSV或Excel格式
        try:
            logs = self.get_logs(filters, limit=1000)  # 导出最多1000条记录
            # 导出逻辑，这里简化为返回日志列表
            return True, logs
        except Exception as e:
            return False, str(e) 