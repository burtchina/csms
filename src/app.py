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

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置环境变量以抑制cryptography警告
os.environ['PYTHONWARNINGS'] = 'ignore:.*TripleDES.*:DeprecationWarning'
os.environ['PYTHONWARNINGS'] = 'ignore:.*Blowfish.*:DeprecationWarning'
os.environ['CRYPTOGRAPHY_SUPPRESS_DEPRECATION_WARNINGS'] = '1'

# 忽略Cryptography和Paramiko相关警告
warnings.filterwarnings('ignore', category=DeprecationWarning, module='cryptography')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='paramiko')
warnings.filterwarnings('ignore', message='.*TripleDES.*')
warnings.filterwarnings('ignore', message='.*Blowfish.*')

# 将项目根目录添加到Python路径中
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
logger.debug(f"项目根目录: {base_dir}")

from flask import Flask, render_template, redirect, url_for, request, send_from_directory, jsonify
from flask_login import current_user, login_required
from functools import wraps
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

def create_app(config_name=None):
    """
    创建Flask应用实例
    
    Args:
        config_name: 配置名称，默认为None，将使用默认配置
        
    Returns:
        Flask应用实例
    """
    logger.debug(f"开始创建应用，配置名称: {config_name}")
    
    # 创建应用实例
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'src', 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    # 确保数据目录存在
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 加载配置
    app.config.from_object('src.config.Config')
    
    # 明确设置数据库URI
    sqlite_db_path = os.path.join(data_dir, 'dev.sqlite')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_db_path}'
    
    # 设置秘钥
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'csms-dev-key-2023'
    
    # 初始化扩展
    from src.core.db import db, login_manager
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)
    
    # 初始化CSRFProtect
    csrf = CSRFProtect(app)
    
    # 登录管理器初始化
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录再访问此页面'
    login_manager.login_message_category = 'warning'
    
    # 导入并使用models
    with app.app_context():
        from src.modules.auth.models import User
        from src.models.device import Device, DeviceType
        from src.models.maintenance import MaintenanceRecord, InspectionReport, InspectionItem
        
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
    from src.modules.policy import init_app as init_policy, policy_template_bp, policy_deploy_bp
    
    # 导入增强版监控蓝图
    try:
        from src.modules.performance.enhanced_monitor_routes import enhanced_monitor_bp
        has_enhanced_monitor = True
    except ImportError:
        logger.warning("增强版监控模块未找到，将不会加载此功能")
        has_enhanced_monitor = False
    
    # 导入实时监控调试蓝图
    try:
        from src.modules.performance.realtime_monitor import realtime_debug_bp
        has_realtime_debug = True
    except ImportError:
        logger.warning("实时监控调试模块未找到，将不会加载此功能")
        has_realtime_debug = False
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(device_bp, url_prefix='/device')
    app.register_blueprint(fault_bp, url_prefix='/fault')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(performance_bp, url_prefix='/performance')
    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 初始化策略管理模块
    init_policy(app)
    logger.info("已注册IPSec与防火墙联动策略管理模块")
    
    # 初始化系统预设策略模板
    try:
        from src.init_policy_templates import init_policy_templates
        # 确保在应用上下文中执行
        with app.app_context():
            init_policy_templates()
        logger.info("已初始化IPSec与防火墙联动策略系统预设模板")
    except Exception as e:
        logger.warning(f"初始化IPSec与防火墙联动策略系统预设模板失败: {str(e)}")
    
    # 注册增强版监控蓝图
    if has_enhanced_monitor:
        app.register_blueprint(enhanced_monitor_bp, url_prefix='/enhanced_monitor')
        logger.info("已注册增强版设备监控模块")
    
    # 注册实时监控调试蓝图
    if has_realtime_debug:
        app.register_blueprint(realtime_debug_bp, url_prefix='/realtime_debug')
        logger.info("已注册实时监控调试模块")
    
    # 错误处理
    register_error_handlers(app)
    
    # 添加全局上下文处理器
    @app.context_processor
    def inject_global_vars():
        return {
            'enhanced_monitor_available': has_enhanced_monitor
        }
    
    # 首页路由
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    # 设备API路由
    @app.route('/devices/api/devices')
    @login_required
    def get_devices_api():
        """全局设备API路由，提供设备列表数据"""
        try:
            from src.models.device import Device
            devices = Device.query.all()
            
            data = []
            for device in devices:
                device_data = {
                    'id': device.id,
                    'name': device.name,
                    'type': str(device.type) if hasattr(device, 'type') else '',
                    'status': device.status if hasattr(device, 'status') else ''
                }
                data.append(device_data)
            
            return jsonify({
                'status': 'success',
                'message': '获取设备列表成功',
                'data': data
            })
        
        except Exception as e:
            logger.error(f"获取设备列表出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'获取设备列表失败: {str(e)}'
            }), 500
    
    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        try:
            # 使用完全限定的模型路径避免冲突
            from src.models.device import Device
            
            # 获取设备总数和状态统计
            device_count = Device.query.count()
            normal_count = Device.query.filter_by(status='正常').count()
            maintenance_count = Device.query.filter_by(status='维修中').count()
            inactive_count = Device.query.filter_by(status='闲置').count()
            retired_count = Device.query.filter_by(status='报废').count()
            
            # 获取最近添加的设备
            recent_devices = Device.query.order_by(Device.id.desc()).limit(5).all()
            
            return render_template(
                'dashboard.html',
                title="系统仪表板",
                device_count=device_count,
                normal_count=normal_count,
                maintenance_count=maintenance_count,
                inactive_count=inactive_count,
                retired_count=retired_count,
                recent_devices=recent_devices
            )
        except Exception as e:
            logger.error(f"仪表板加载错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return render_template('errors/500.html'), 500
    
    @app.route('/仪表盘')
    def dashboard_cn():
        return redirect(url_for('dashboard'))
    
    @app.route('/performance/realtime')
    def realtime_monitor():
        """实时监控页面"""
        return render_template('dashboard.html')
    
    # 设置内容安全策略
    @app.after_request
    def add_security_headers(response):
        # 允许脚本执行和内联脚本，并添加外部CDN源
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com https://*.datatables.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://*.datatables.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://*.datatables.net; "
            "img-src 'self' data: https://*.datatables.net; "
            "connect-src 'self' https://*.datatables.net; "
            "frame-src 'self';"
        )
        return response
    
    return app

def create_tables_and_sample_data(app):
    """
    创建数据库表和示例数据
    
    Args:
        app: Flask应用实例
    """
    with app.app_context():
        try:
            from src.modules.auth.models import User
            from src.core.db import db
            
            logger.info(f"正在使用数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].split('sqlite:///')[-1]
            logger.info(f"数据库文件路径: {db_path}")
            
            # 检查是否需要初始化数据库
            db_exists = os.path.exists(db_path) and os.path.getsize(db_path) > 0
            
            # 确保数据库表存在
            db.create_all()
            
            # 仅在数据库不存在时添加示例用户
            if not db_exists:
                logger.info("数据库不存在，正在初始化...")
                # 添加示例用户
                admin_user = User.query.filter_by(username='admin').first()
                test_user = User.query.filter_by(username='test').first()
                
                if not admin_user:
                    logger.info("创建管理员用户...")
                    admin = User(username='admin', email='admin@example.com', password='admin123')
                    admin.is_admin = True
                    db.session.add(admin)
                    
                if not test_user:
                    logger.info("创建测试用户...")
                    test_user = User(username='test', email='test@example.com', password='test123')
                    db.session.add(test_user)
                    
                db.session.commit()
                logger.info("数据库初始化成功！")
            else:
                logger.info("使用现有数据库，跳过初始化步骤")
        except Exception as e:
            db.session.rollback()
            logger.error(f"数据库初始化错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404错误: {request.path}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500错误: {str(error)}")
        return render_template('errors/500.html'), 500
    
    logger.debug("错误处理器注册完成")

# 全局应用实例
_app_instance = None

def get_app():
    """获取全局Flask应用实例
    
    如果实例不存在，则创建一个新的应用实例
    
    Returns:
        Flask应用实例
    """
    global _app_instance
    if _app_instance is None:
        _app_instance = create_app()
    return _app_instance

# 如果直接运行此文件
if __name__ == '__main__':
    # 创建应用
    app = create_app()
    
    # 创建数据库表和示例数据
    create_tables_and_sample_data(app)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='校园安全管理系统启动脚本')
    parser.add_argument('--reset-db', action='store_true', help='重置数据库（删除所有数据并重建）')
    parser.add_argument('--port', type=int, default=5000, help='指定端口号，默认5000')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址，默认0.0.0.0')
    args = parser.parse_args()
    
    # 如果指定了重置数据库参数
    if args.reset_db:
        with app.app_context():
            logger.info("正在重置数据库...")
            # 删除数据库文件
            sqlite_db_path = os.path.join(base_dir, 'data', 'dev.sqlite')
            if os.path.exists(sqlite_db_path):
                try:
                    os.remove(sqlite_db_path)
                    logger.info(f"已删除数据库文件: {sqlite_db_path}")
                except Exception as e:
                    logger.error(f"删除数据库文件失败: {str(e)}")
            
            # 重新创建数据库
            create_tables_and_sample_data(app)
    
    # 打印资源路径信息
    logger.info(f"应用已启动，访问 http://127.0.0.1:{args.port}")
    logger.info(f"模板目录: {app.template_folder}")
    logger.info(f"静态文件目录: {app.static_folder}")
    
    app.run(host=args.host, port=args.port, debug=True) 