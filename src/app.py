#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 应用入口
"""

import os
import sys
import argparse
import logging
import warnings
import importlib

# 设置环境变量以抑制cryptography警告
os.environ['PYTHONWARNINGS'] = 'ignore:.*TripleDES.*:DeprecationWarning'
os.environ['PYTHONWARNINGS'] = 'ignore:.*Blowfish.*:DeprecationWarning'
os.environ['CRYPTOGRAPHY_SUPPRESS_DEPRECATION_WARNINGS'] = '1'

# 忽略Cryptography和Paramiko相关警告
warnings.filterwarnings('ignore', category=DeprecationWarning, module='cryptography')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='paramiko')
warnings.filterwarnings('ignore', message='.*TripleDES.*')
warnings.filterwarnings('ignore', message='.*Blowfish.*')

# 将src目录添加到Python路径中
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_required
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from src.core.db import db, login_manager

# 确保数据目录存在
data_dir = os.path.join(base_dir, 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 创建应用实例
# 注意为了测试方便，使用项目根目录的templates和static
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'src', 'templates'),
            static_folder=os.path.join(base_dir, 'static'))

# 加载配置
app.config.from_object('src.config.Config')

# 明确设置数据库URI
sqlite_db_path = os.path.join(data_dir, 'dev.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_db_path}'

# 设置秘钥
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'csms-dev-key-2023'

# 初始化扩展
db.init_app(app)
login_manager.init_app(app)

# 登录管理器初始化
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问此页面'
login_manager.login_message_category = 'warning'

# 导入并使用models
with app.app_context():
    from src.modules.auth.models import User
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户的回调函数"""
        return User.query.get(int(user_id))

# 注册蓝图
from src.modules.auth.routes import auth_bp
from src.modules.device import device_bp
from src.modules.fault.routes import fault_bp
from src.modules.maintenance.routes import maintenance_bp
from src.modules.performance.routes import performance_bp
from src.modules.system.routes import system_bp
from src.api import api_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(device_bp, url_prefix='/device')
app.register_blueprint(fault_bp, url_prefix='/fault')
app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
app.register_blueprint(performance_bp, url_prefix='/performance')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(api_bp, url_prefix='/api')

# 错误处理
@app.errorhandler(404)
def page_not_found(error):
    return f"<h1>404 - 页面未找到</h1><p>请检查URL是否正确</p>", 404

@app.errorhandler(500)
def internal_server_error(error):
    return f"<h1>500 - 服务器内部错误</h1><p>服务器处理请求时出错</p>", 500

# 首页路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/仪表盘')
def dashboard_cn():
    return redirect(url_for('dashboard'))

@app.route('/performance/realtime')
def realtime_monitor():
    """实时监控页面"""
    return render_template('dashboard.html')

# 创建数据库表和示例数据
def create_tables_and_sample_data():
    try:
        from src.modules.auth.models import User
        
        print(f"正在使用数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"数据库文件路径: {sqlite_db_path}")
        
        # 检查是否需要初始化数据库
        db_exists = os.path.exists(sqlite_db_path) and os.path.getsize(sqlite_db_path) > 0
        
        # 确保数据库表存在
        db.create_all()
        
        # 仅在数据库不存在时添加示例用户
        if not db_exists:
            print("数据库不存在，正在初始化...")
            # 添加示例用户
            admin_user = User.query.filter_by(username='admin').first()
            test_user = User.query.filter_by(username='test').first()
            
            if not admin_user:
                print("创建管理员用户...")
                admin = User(username='admin', email='admin@example.com', password='admin123')
                admin.is_admin = True
                db.session.add(admin)
                
            if not test_user:
                print("创建测试用户...")
                test_user = User(username='test', email='test@example.com', password='test123')
                db.session.add(test_user)
                
            db.session.commit()
            print("数据库初始化成功！")
        else:
            print("使用现有数据库，跳过初始化步骤")
    except Exception as e:
        db.session.rollback()
        print(f"数据库初始化错误: {e}")
        import traceback
        traceback.print_exc()

# 初始化数据库（如果不存在）
with app.app_context():
    # 创建表并添加示例数据（如果需要）
    create_tables_and_sample_data()

# 应用启动
if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='校园安全管理系统启动脚本')
    parser.add_argument('--reset-db', action='store_true', help='重置数据库（删除所有数据并重建）')
    parser.add_argument('--port', type=int, default=5000, help='指定端口号，默认5000')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址，默认0.0.0.0')
    args = parser.parse_args()
    
    # 如果指定了重置数据库参数
    if args.reset_db:
        with app.app_context():
            print("正在重置数据库...")
            # 删除数据库文件
            if os.path.exists(sqlite_db_path):
                try:
                    os.remove(sqlite_db_path)
                    print(f"已删除数据库文件: {sqlite_db_path}")
                except Exception as e:
                    print(f"删除数据库文件失败: {e}")
            
            # 重新创建数据库
            create_tables_and_sample_data()
    
    # 打印资源路径信息
    print(f"应用已启动，访问 http://127.0.0.1:{args.port}")
    print(f"模板目录: {app.template_folder}")
    print(f"静态文件目录: {app.static_folder}")
    
    app.run(host=args.host, port=args.port, debug=True) 