#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
为用户表添加缺少的字段
"""

import os
import sys
import logging
import sqlite3

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 项目根目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"项目根目录: {base_dir}")

def add_user_fields():
    """添加用户表缺少的字段"""
    data_dir = os.path.join(base_dir, 'data')
    db_path = os.path.join(data_dir, 'dev.sqlite')
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    logger.info(f"正在连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查users表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        logger.error("users表不存在")
        conn.close()
        return False
    
    # 获取users表的当前结构
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    logger.info(f"当前用户表列: {columns}")
    
    # 需要添加的字段
    new_fields = [
        ("display_name", "VARCHAR(64)"),
        ("phone", "VARCHAR(20)"),
        ("role", "VARCHAR(20)"),
        ("last_login", "DATETIME")
    ]
    
    # 添加缺少的字段
    for field_name, field_type in new_fields:
        if field_name not in columns:
            try:
                logger.info(f"添加字段: {field_name} ({field_type})")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                logger.info(f"字段 {field_name} 添加成功")
            except sqlite3.OperationalError as e:
                logger.error(f"添加字段 {field_name} 失败: {str(e)}")
                conn.rollback()
                conn.close()
                return False
    
    # 提交更改
    conn.commit()
    logger.info("所有字段添加完成")
    
    # 查看更新后的表结构
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    logger.info("更新后的用户表结构:")
    for col in columns:
        logger.info(f"  {col[1]} ({col[2]})")
    
    conn.close()
    return True

if __name__ == "__main__":
    logger.info("开始向用户表添加缺失字段...")
    if add_user_fields():
        logger.info("字段添加成功！")
    else:
        logger.error("字段添加失败！") 