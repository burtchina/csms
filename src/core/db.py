#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库配置和扩展
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# 创建数据库实例
db = SQLAlchemy()

# 创建数据库迁移实例
migrate = Migrate()

# 创建登录管理器实例
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问此页面'
login_manager.login_message_category = 'warning'

def init_db(app):
    """初始化数据库和扩展"""
    # 初始化SQLAlchemy
    db.init_app(app)
    
    # 初始化Migrate
    migrate.init_app(app, db)
    
    # 初始化LoginManager
    login_manager.init_app(app)
    
    # 设置用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        from src.modules.auth.models import User
        return User.query.get(int(user_id)) 