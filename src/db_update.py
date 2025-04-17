#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库更新脚本 - 添加设备表中缺失的列
"""

import os
import sqlite3
from pathlib import Path

# 获取基础目录
base_dir = Path(__file__).parent.parent

# 数据目录
data_dir = base_dir / 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 数据库文件路径
DB_PATH = data_dir / 'dev.sqlite'

def add_missing_columns():
    """添加设备表中缺失的列"""
    print(f"正在连接数据库: {DB_PATH}")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查数据库中的表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"数据库中的表: {tables}")
    
    # 检查devices表是否存在
    if ('devices',) in tables:
        # 获取devices表的列信息
        cursor.execute("PRAGMA table_info(devices)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"devices表现有列: {column_names}")
        
        # 需要添加的列列表
        columns_to_add = [
            ("username", "VARCHAR(50)"),
            ("password", "VARCHAR(100)"),
            ("manufacturer", "VARCHAR(100)"),
            ("model", "VARCHAR(100)"),
            ("serial_number", "VARCHAR(100)"),
            ("purchase_date", "DATE"),
            ("warranty_period", "INTEGER"),
            ("last_maintenance", "DATETIME"),
            ("next_maintenance", "DATETIME")
        ]
        
        # 添加缺失的列
        added_columns = []
        for column_name, column_type in columns_to_add:
            if column_name not in column_names:
                try:
                    cursor.execute(f"ALTER TABLE devices ADD COLUMN {column_name} {column_type}")
                    added_columns.append(column_name)
                    print(f"已添加列: {column_name} ({column_type})")
                except sqlite3.OperationalError as e:
                    print(f"添加列 {column_name} 时出错: {e}")
        
        if added_columns:
            conn.commit()
            print(f"数据库更新完成，添加了以下列: {', '.join(added_columns)}")
        else:
            print("所有必要的列已存在，无需更新")
    else:
        print("devices表不存在，无需更新")
    
    # 关闭数据库连接
    conn.close()

if __name__ == "__main__":
    add_missing_columns() 