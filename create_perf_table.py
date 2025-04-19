#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建性能数据表脚本
仅添加缺失的performance_data表，不影响现有数据
"""

import os
import sys
from sqlalchemy import inspect

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

try:
    from src.app import app, db
    from src.modules.performance.models import PerformanceData
    
    print("正在检查并创建性能数据表...")
    
    with app.app_context():
        # 使用SQLAlchemy的inspect来检查表是否存在
        inspector = inspect(db.engine)
        if 'performance_data' not in inspector.get_table_names():
            print("创建性能数据表...")
            # 创建表
            db.create_all(tables=[PerformanceData.__table__])
            print("性能数据表创建成功！")
        else:
            print("性能数据表已存在，无需创建。")
        
except Exception as e:
    print(f"创建性能数据表时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("操作完成！") 