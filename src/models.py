#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库模型导入文件
"""

# 这个文件用于导入所有模型，确保它们被SQLAlchemy发现
# 通过db.py中的init_db函数导入模型，避免循环导入问题

# 导入所有模型，确保它们被SQLAlchemy发现
from src.modules.auth.models import User 