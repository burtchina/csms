from typing import Dict, List, Any
from sqlalchemy import desc
from src.core.db import db


class PolicyAuditLogRepository:
    """策略审计日志仓库类"""

    def __init__(self, session=None):
        """
        初始化仓库
        
        Args:
            session: 数据库会话
        """
        self.session = session if session else db.session
    
    def create(self, log_data: Dict[str, Any]) -> Any:
        """
        创建审计日志
        
        Args:
            log_data: 日志数据
            
        Returns:
            Any: 创建的审计日志对象
        """
        from src.modules.policy.models.policy_audit_log import PolicyAuditLog
        
        log = PolicyAuditLog(**log_data)
        self.session.add(log)
        self.session.commit()
        return log
    
    def get(self, log_id: int) -> Any:
        """
        获取单个审计日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            Any: 审计日志对象
        """
        from src.modules.policy.models.policy_audit_log import PolicyAuditLog
        
        return self.session.query(PolicyAuditLog).filter_by(id=log_id).first()
    
    def get_all(self, filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Any]:
        """
        获取审计日志列表
        
        Args:
            filters: 过滤条件
            limit: 最大返回记录数
            offset: 起始记录索引
            
        Returns:
            List[Any]: 审计日志列表
        """
        from src.modules.policy.models.policy_audit_log import PolicyAuditLog
        
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
            if 'ip_address' in filters:
                query = query.filter(PolicyAuditLog.ip_address == filters['ip_address'])
        
        # 按创建时间降序排序
        query = query.order_by(desc(PolicyAuditLog.created_at))
        
        # 应用分页
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        return query.all()
    
    def get_logs_by_policy(self, policy_id: int, limit: int = 100) -> List[Any]:
        """
        获取指定策略的审计日志
        
        Args:
            policy_id: 策略ID
            limit: 最大返回记录数
            
        Returns:
            List[Any]: 审计日志列表
        """
        filters = {'policy_id': policy_id}
        return self.get_all(filters, limit)
    
    def get_logs_by_user(self, user_id: int, limit: int = 100) -> List[Any]:
        """
        获取指定用户的审计日志
        
        Args:
            user_id: 用户ID
            limit: 最大返回记录数
            
        Returns:
            List[Any]: 审计日志列表
        """
        filters = {'user_id': user_id}
        return self.get_all(filters, limit)
    
    def delete(self, log_id: int) -> bool:
        """
        删除审计日志
        
        Args:
            log_id: 日志ID
            
        Returns:
            bool: 是否成功
        """
        from src.modules.policy.models.policy_audit_log import PolicyAuditLog
        
        log = self.session.query(PolicyAuditLog).filter_by(id=log_id).first()
        if not log:
            return False
        
        self.session.delete(log)
        self.session.commit()
        return True 