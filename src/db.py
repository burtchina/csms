#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库实例
这个文件用于存放SQLAlchemy实例，避免循环导入问题
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 创建数据库实例
db = SQLAlchemy()
migrate = None

def init_db(app):
    """初始化数据库"""
    global migrate
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 导入所有模型，确保它们被SQLAlchemy注册
    from src.modules.auth.models import User
    from src.modules.device.models import Device, DeviceType
    
    return db 