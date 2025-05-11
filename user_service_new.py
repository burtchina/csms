#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户服务类
提供用户相关的业务逻辑
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