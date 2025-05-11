#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户服务模块：提供用户相关的业务逻辑处理
"""

from typing import Dict, Any, Tuple
from src.modules.auth.models import User
from src.db import db


class UserService:
    """用户服务类"""
    
    def get_user_by_id(self, user_id: int) -> Tuple[bool, Any]:
        """通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在"
            return True, user
        except Exception as e:
            return False, str(e)
    
    def get_user_by_username(self, username: str) -> Tuple[bool, Any]:
        """通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        """
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return False, "用户不存在"
            return True, user
        except Exception as e:
            return False, str(e)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 更新数据
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        """
        try:
            success, result = self.get_user_by_id(user_id)
            if not success:
                return False, result
            
            user = result
            
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            db.session.commit()
            return True, user
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def create_user(self, user_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """创建用户
        
        Args:
            user_data: 用户数据
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        """
        try:
            # 检查用户名是否已存在
            success, result = self.get_user_by_username(user_data.get('username', ''))
            if success:
                return False, "用户名已存在"
            
            user = User(**user_data)
            db.session.add(user)
            db.session.commit()
            return True, user
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def delete_user(self, user_id: int) -> Tuple[bool, Any]:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, Any]: (成功状态, 删除结果信息)
        """
        try:
            success, result = self.get_user_by_id(user_id)
            if not success:
                return False, result
            
            user = result
            db.session.delete(user)
            db.session.commit()
            return True, "用户删除成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)