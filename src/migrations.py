#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移工具
"""

import os
import sys
import logging
from flask_migrate import Migrate, MigrateCommand

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到Python路径中
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
logger.debug(f"项目根目录: {base_dir}")

from src.app import create_app
from src.core.db import db

app = create_app()
migrate = Migrate(app, db)

def init_migrations():
    """初始化迁移环境"""
    with app.app_context():
        logger.info("初始化迁移环境...")
        os.system(f"flask db init")

def create_migration(message):
    """创建迁移脚本"""
    with app.app_context():
        logger.info(f"创建迁移脚本: {message}...")
        os.system(f"flask db migrate -m \"{message}\"")

def apply_migration():
    """应用迁移"""
    with app.app_context():
        logger.info("应用迁移...")
        os.system(f"flask db upgrade")

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("--init", action="store_true", help="初始化迁移环境")
    parser.add_argument("--migrate", help="创建迁移脚本")
    parser.add_argument("--upgrade", action="store_true", help="应用迁移")
    args = parser.parse_args()

    if args.init:
        init_migrations()
    elif args.migrate:
        create_migration(args.migrate)
    elif args.upgrade:
        apply_migration()
    else:
        parser.print_help() 