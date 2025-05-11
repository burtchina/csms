#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略服务类
提供策略相关的业务逻辑
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from src.core.db import db
from src.modules.policy.models.policy import Policy
from src.modules.policy.repositories.policy_repository import PolicyRepository, PolicyAuditLogRepository
from src.modules.policy.validators.policy_validator import PolicyValidator


class PolicyService:
    """策略服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.policy_repo = PolicyRepository(db.session)
        self.audit_repo = PolicyAuditLogRepository(db.session)
    
    def create_policy(self, policy_data: Dict[str, Any], user_id: int) -> Tuple[bool, Any]:
        """创建新策略
        
        Args:
            policy_data: 策略数据
            user_id: 操作用户ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 设置创建人和创建时间
        policy_data['created_by'] = user_id
        policy_data['created_at'] = datetime.utcnow()
        policy_data['updated_at'] = datetime.utcnow()
        policy_data['status'] = policy_data.get('status', 'draft')
        
        # 验证策略数据
        is_valid, error = PolicyValidator.validate_policy(policy_data)
        if not is_valid:
            return False, {'error': error}
        
        try:
            # 创建策略
            policy = self.policy_repo.create(policy_data)
            
            # 创建审计日志
            self._create_audit_log(
                policy_id=policy.id,
                user_id=user_id,
                action='create',
                details=f'创建策略 {policy.name}'
            )
            
            return True, policy
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def update_policy(self, policy_id: int, policy_data: Dict[str, Any], user_id: int) -> Tuple[bool, Any]:
        """更新策略
        
        Args:
            policy_id: 策略ID
            policy_data: 策略数据
            user_id: 操作用户ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 获取现有策略
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        # 不能修改已删除的策略
        if policy.status == 'deleted':
            return False, {'error': '策略已删除，无法修改'}
        
        # 更新时间
        policy_data['updated_at'] = datetime.utcnow()
        
        # 如果更新了配置，需要验证
        if 'config' in policy_data:
            # 构建完整策略数据进行验证
            validate_data = {
                'name': policy_data.get('name', policy.name),
                'type': policy_data.get('type', policy.type),
                'config': policy_data['config']
            }
            
            is_valid, error = PolicyValidator.validate_policy(validate_data)
            if not is_valid:
                return False, {'error': error}
        
        try:
            # 更新策略
            updated_policy = self.policy_repo.update(policy_id, policy_data)
            
            # 创建审计日志
            self._create_audit_log(
                policy_id=policy_id,
                user_id=user_id,
                action='update',
                details=f'更新策略 {updated_policy.name}'
            )
            
            return True, updated_policy
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def delete_policy(self, policy_id: int, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """删除策略（逻辑删除）
        
        Args:
            policy_id: 策略ID
            user_id: 操作用户ID
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (是否成功, 结果/错误信息)
        """
        # 获取现有策略
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        # 已删除的策略不能再删除
        if policy.status == 'deleted':
            return False, {'error': '策略已删除'}
        
        try:
            # 逻辑删除策略
            success = self.policy_repo.delete(policy_id)
            if not success:
                return False, {'error': '删除策略失败'}
            
            # 创建审计日志
            self._create_audit_log(
                policy_id=policy_id,
                user_id=user_id,
                action='delete',
                details=f'删除策略 {policy.name}'
            )
            
            return True, {'message': '策略已删除'}
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def get_policy(self, policy_id: int) -> Tuple[bool, Any]:
        """获取策略详情
        
        Args:
            policy_id: 策略ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        return True, policy
    
    def list_policies(self, filters: Dict[str, Any] = None) -> List[Policy]:
        """获取策略列表
        
        Args:
            filters: 过滤条件
            
        Returns:
            List[Policy]: 策略列表
        """
        # 默认不显示已删除的策略
        if filters is None:
            filters = {}
        
        if 'status' not in filters:
            # 默认显示所有非deleted状态的策略
            filters['status_not'] = 'deleted'
        
        return self.policy_repo.get_all(filters)
    
    def validate_policy_config(self, policy_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证策略配置
        
        Args:
            policy_type: 策略类型
            config: 策略配置
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not policy_type:
            return {'success': False, 'errors': ['策略类型不能为空']}
        
        if not config:
            return {'success': False, 'errors': ['策略配置不能为空']}
        
        # 构建验证数据
        validate_data = {
            'name': 'temp_policy_for_validation',
            'type': policy_type,
            'config': config
        }
        
        # 验证策略数据
        is_valid, error = PolicyValidator.validate_policy(validate_data)
        
        if is_valid:
            return {'success': True}
        else:
            # 确保错误信息是列表格式
            if isinstance(error, str):
                return {'success': False, 'errors': [error]}
            elif isinstance(error, list):
                return {'success': False, 'errors': error}
            else:
                return {'success': False, 'errors': ['验证失败，未知错误']}
    
    def _create_audit_log(self, policy_id: int, user_id: int, action: str, details: str) -> None:
        """创建审计日志
        
        Args:
            policy_id: 策略ID
            user_id: 用户ID
            action: 操作类型
            details: 详情
        """
        log_data = {
            'policy_id': policy_id,
            'user_id': user_id,
            'action': action,
            'details': details,
            'created_at': datetime.utcnow()
        }
        
        self.audit_repo.create(log_data) 