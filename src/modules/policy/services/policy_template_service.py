#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略模板服务类
提供策略模板相关的业务逻辑
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from src.core.db import db
from src.modules.policy.models.policy_template import PolicyTemplate
from src.modules.policy.repositories.policy_repository import PolicyTemplateRepository
from src.modules.policy.validators.policy_validator import PolicyValidator


class PolicyTemplateService:
    """策略模板服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.template_repo = PolicyTemplateRepository(db.session)
    
    def create_template(self, template_data: Dict[str, Any], user_id: int) -> Tuple[bool, Any]:
        """创建新策略模板
        
        Args:
            template_data: 模板数据
            user_id: 创建用户ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 设置创建人
        template_data['created_by'] = user_id
        template_data['created_at'] = datetime.utcnow()
        
        # 验证配置数据
        if 'config' in template_data and 'type' in template_data:
            validate_data = {
                'name': template_data.get('name', ''),
                'type': template_data['type'],
                'config': template_data['config']
            }
            
            is_valid, error = PolicyValidator.validate_policy(validate_data)
            if not is_valid:
                return False, {'error': error}
        
        try:
            # 创建模板
            template = self.template_repo.create(template_data)
            return True, template
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def update_template(self, template_id: int, template_data: Dict[str, Any], user_id: int) -> Tuple[bool, Any]:
        """更新策略模板
        
        Args:
            template_id: 模板ID
            template_data: 模板数据
            user_id: 更新用户ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 获取现有模板
        template = self.template_repo.get(template_id)
        if not template:
            return False, {'error': '模板不存在'}
        
        # 系统预设模板不允许修改
        if template.is_system:
            return False, {'error': '系统预设模板不允许修改'}
        
        # 验证配置数据
        if 'config' in template_data:
            validate_data = {
                'name': template_data.get('name', template.name),
                'type': template_data.get('type', template.type),
                'config': template_data['config']
            }
            
            is_valid, error = PolicyValidator.validate_policy(validate_data)
            if not is_valid:
                return False, {'error': error}
        
        try:
            # 更新模板
            updated_template = self.template_repo.update(template_id, template_data)
            if not updated_template:
                return False, {'error': '更新模板失败'}
            
            return True, updated_template
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def delete_template(self, template_id: int) -> Tuple[bool, Dict[str, Any]]:
        """删除策略模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (是否成功, 结果/错误信息)
        """
        # 获取现有模板
        template = self.template_repo.get(template_id)
        if not template:
            return False, {'error': '模板不存在'}
        
        # 系统预设模板不允许删除
        if template.is_system:
            return False, {'error': '系统预设模板不允许删除'}
        
        try:
            # 删除模板
            success = self.template_repo.delete(template_id)
            if not success:
                return False, {'error': '删除模板失败'}
            
            return True, {'message': '模板已删除'}
        except Exception as e:
            db.session.rollback()
            return False, {'error': str(e)}
    
    def get_template(self, template_id: int) -> Tuple[bool, Any]:
        """获取模板详情
        
        Args:
            template_id: 模板ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        template = self.template_repo.get(template_id)
        if not template:
            return False, {'error': '模板不存在'}
        
        return True, template
    
    def list_templates(self, filters: Dict[str, Any] = None) -> List[PolicyTemplate]:
        """获取模板列表
        
        Args:
            filters: 过滤条件
            
        Returns:
            List[PolicyTemplate]: 模板列表
        """
        return self.template_repo.get_all(filters) 