import os
import shutil

# 定义文件内容
content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户服务类
提供用户相关的业务逻辑
\"\"\"

from typing import Dict, Any, Tuple

from src.modules.auth.models import User
from src.db import db


class UserService:
    \"\"\"用户服务类\"\"\"
    
    def get_user_by_id(self, user_id: int) -> Tuple[bool, Any]:
        \"\"\"通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        \"\"\"
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "用户不存在"
            return True, user
        except Exception as e:
            return False, str(e)
    
    def get_user_by_username(self, username: str) -> Tuple[bool, Any]:
        \"\"\"通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        \"\"\"
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return False, "用户不存在"
            return True, user
        except Exception as e:
            return False, str(e)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Tuple[bool, Any]:
        \"\"\"更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 用户数据
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        \"\"\"
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
        \"\"\"创建用户
        
        Args:
            user_data: 用户数据
            
        Returns:
            Tuple[bool, Any]: (成功状态, 用户对象或错误信息)
        \"\"\"
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
        \"\"\"删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Tuple[bool, Any]: (成功状态, 成功消息或错误信息)
        \"\"\"
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
"""

# 目标文件
target_file = 'src/modules/auth/services/user_service.py'

# 创建临时文件
temp_file = 'temp_user_service.py'
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 备份原文件
backup_file = target_file + '.bak'
try:
    if os.path.exists(backup_file):
        os.remove(backup_file)
    shutil.copy2(target_file, backup_file)
    print(f"备份原文件到 {backup_file}")
except Exception as e:
    print(f"备份原文件失败: {e}")
    
# 替换文件
try:
    shutil.copy2(temp_file, target_file)
    print(f"成功替换文件 {target_file}")
except Exception as e:
    print(f"替换文件失败: {e}")
    
# 清理临时文件
try:
    os.remove(temp_file)
    print(f"清理临时文件 {temp_file}")
except Exception as e:
    print(f"清理临时文件失败: {e}")

print("操作完成!") 