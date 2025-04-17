#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
用于手动初始化或重置数据库
"""

import os
import sys
import shutil
from datetime import datetime

# 获取项目根目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# 数据库文件路径
data_dir = os.path.join(base_dir, 'data')
sqlite_db_path = os.path.join(data_dir, 'dev.sqlite')

# 确保数据目录存在
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"已创建数据目录: {data_dir}")

# 询问用户是否要重置数据库
reset_db = False
if os.path.exists(sqlite_db_path):
    choice = input(f"数据库已存在。选择操作:\n1. 使用现有数据库\n2. 创建备份并重置\n3. 直接重置（数据将丢失）\n请选择(1/2/3): ")
    
    if choice == '2':
        # 创建备份目录
        backup_dir = os.path.join(data_dir, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 创建带时间戳的备份文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = os.path.join(backup_dir, f"dev_sqlite_backup_{timestamp}.db")
        
        # 复制数据库文件作为备份
        try:
            shutil.copy2(sqlite_db_path, backup_path)
            print(f"数据库已备份至: {backup_path}")
            reset_db = True
        except Exception as e:
            print(f"备份数据库失败: {e}")
            sys.exit(1)
    elif choice == '3':
        reset_db = True
    else:
        print("使用现有数据库，不进行重置。")
        sys.exit(0)
else:
    print("未发现现有数据库，将创建新数据库。")
    reset_db = True

# 如果需要重置，删除现有数据库
if reset_db and os.path.exists(sqlite_db_path):
    try:
        os.remove(sqlite_db_path)
        print(f"已删除现有数据库: {sqlite_db_path}")
    except Exception as e:
        print(f"删除数据库失败: {e}")
        sys.exit(1)

# 初始化Flask应用
try:
    from src.app import app, db
    from src.modules.auth.models import User
except ImportError as e:
    print(f"导入应用失败: {e}")
    print("请确保您在项目根目录下运行此脚本")
    sys.exit(1)

print("正在初始化数据库...")

try:
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("已创建数据库表结构")
        
        # 检查是否需要创建初始用户
        admin_user = User.query.filter_by(username='admin').first()
        test_user = User.query.filter_by(username='test').first()
        
        if not admin_user:
            print("创建管理员用户...")
            admin = User(username='admin', email='admin@example.com', password='admin123')
            admin.is_admin = True
            db.session.add(admin)
        else:
            print("管理员用户已存在，跳过创建")
        
        if not test_user:
            print("创建测试用户...")
            test_user = User(username='test', email='test@example.com', password='test123')
            db.session.add(test_user)
        else:
            print("测试用户已存在，跳过创建")
        
        # 提交更改
        db.session.commit()
        print("数据库初始化完成！")
        print("可用账号:")
        print(" - 管理员: admin / admin123")
        print(" - 测试用户: test / test123")
        
except Exception as e:
    print(f"数据库初始化错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n数据库已准备就绪!")
print(f"数据库路径: {sqlite_db_path}")
print("现在可以启动应用: python src/app.py") 