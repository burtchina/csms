#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
权限服务模块
提供权限验证功能
"""

from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity

from src.core.models import Role, User
from src.core.db import db

def check_permission(permission_code):
    """
    检查当前用户是否具有指定权限
    
    Args:
        permission_code (str): 权限代码，如 'policy:view'
        
    Returns:
        bool: 是否具有权限
    """
    try:
        # 获取当前用户
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return False
            
        # 超级管理员具有所有权限
        if user.is_admin:
            return True
            
        # 获取用户角色
        role = Role.query.get(user.role_id)
        if not role:
            return False
            
        # 检查角色是否有指定权限
        return role.has_permission(permission_code)
    except Exception as e:
        print(f"权限检查异常: {str(e)}")
        return False
        
def require_permission(permission_code):
    """
    权限验证装饰器
    
    Args:
        permission_code (str): 权限代码，如 'policy:view'
        
    Returns:
        function: 装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(permission_code):
                return jsonify({
                    'status': 'error',
                    'message': '没有操作权限'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator 