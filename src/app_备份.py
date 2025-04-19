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
from sqlalchemy import inspect
from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_required
from functools import wraps

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录添加到Python路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.debug(f"项目根目录: {base_dir}")
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
    logger.debug(f"已添加项目根目录到Python路径")

# 设置环境变量以抑制cryptography警告
os.environ['PYTHONWARNINGS'] = 'ignore:.*TripleDES.*:DeprecationWarning'
os.environ['PYTHONWARNINGS'] = 'ignore:.*Blowfish.*:DeprecationWarning'
os.environ['CRYPTOGRAPHY_SUPPRESS_DEPRECATION_WARNINGS'] = '1'

# 忽略Cryptography和Paramiko相关警告
warnings.filterwarnings('ignore', category=DeprecationWarning, module='cryptography')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='paramiko')
warnings.filterwarnings('ignore', message='.*TripleDES.*')
warnings.filterwarnings('ignore', message='.*Blowfish.*')

def create_app(config_name=None):
    """
    创建Flask应用实例 - 应用工厂模式
    
    Args:
        config_name: 配置名称，默认为None，将从环境变量获取
        
    Returns:
        Flask应用实例
    """
    logger.debug(f"开始创建应用，配置名称: {config_name}")
    
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')
        logger.debug(f"使用环境变量配置或默认配置: {config_name}")
    
    # 创建Flask应用
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'src', 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    logger.debug(f"已创建Flask应用实例")
    
    # 确保数据目录存在
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    logger.debug(f"确保数据目录存在: {data_dir}")
    
    # 导入配置 - 使用项目根目录的配置文件
    try:
        logger.debug("导入配置模块...")
        from src.config import config as app_config
        logger.debug("成功导入配置模块")
        app.config.from_object(app_config[config_name])
        app_config[config_name].init_app(app)
        
        # 明确设置数据库URI，确保使用正确的文件路径
        sqlite_db_path = os.path.join(data_dir, 'dev.sqlite')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_db_path}'
        logger.debug(f"已应用配置: {config_name}, 数据库路径: {sqlite_db_path}")
    except ImportError as e:
        logger.error(f"导入配置模块失败: {str(e)}")
        raise
    
    # 初始化数据库和扩展
    try:
        logger.debug("导入数据库模块...")
        from src.core.db import db, migrate, login_manager, init_db
        logger.debug("成功导入数据库模块")
        init_db(app)
        logger.debug("已初始化数据库和扩展")
    except ImportError as e:
        logger.error(f"导入数据库模块失败: {str(e)}")
        raise
    
    # 注册蓝图
    logger.debug("开始注册蓝图...")
    register_blueprints(app)
    logger.debug("蓝图注册完成")
    
    # 注册错误处理器
    logger.debug("开始注册错误处理器...")
    register_error_handlers(app)
    logger.debug("错误处理器注册完成")
    
    # 注册主页路由
    logger.debug("开始注册主页路由...")
    register_main_routes(app)
    logger.debug("主页路由注册完成")
    
    # 运行数据库兼容性修复
    logger.debug("开始运行数据库兼容性修复...")
    with app.app_context():
        try:
            from src.migration_utils import run_compatibility_fixes
            logger.debug("成功导入迁移工具模块")
            compatibility_result = run_compatibility_fixes()
            logger.info(f"数据库兼容性检查结果: {compatibility_result}")
        except Exception as e:
            logger.error(f"运行数据库兼容性修复时出错: {str(e)}")
    
    logger.debug("应用创建完成")
    return app

def register_blueprints(app):
    """
    注册所有蓝图
    
    Args:
        app: Flask应用实例
    """
    try:
        # 使用更直接的方式导入蓝图
        logger.debug("导入所有蓝图...")
        
        # 认证模块
        from src.modules.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.debug("已注册auth_bp")
        
        # 设备模块
        from src.modules.device import device_bp
        app.register_blueprint(device_bp, url_prefix='/devices')
        logger.debug("已注册device_bp")
        
        # 性能模块
        from src.modules.performance.views import performance_bp
        app.register_blueprint(performance_bp, url_prefix='/performance')
        logger.debug("已注册performance_bp")
        
        # 检查是否有其他可选模块
        try:
            from src.modules.fault import fault_bp
            app.register_blueprint(fault_bp, url_prefix='/fault')
            logger.debug("已注册fault_bp")
        except ImportError:
            logger.warning("未找到故障模块蓝图，跳过注册")
        
        try:
            from src.modules.maintenance import maintenance_bp
            app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
            logger.debug("已注册maintenance_bp")
        except ImportError:
            logger.warning("未找到维护模块蓝图，跳过注册")
        
        try:
            from src.modules.system import system_bp
            app.register_blueprint(system_bp, url_prefix='/system')
            logger.debug("已注册system_bp")
        except ImportError:
            logger.warning("未找到系统模块蓝图，跳过注册")
        
        logger.debug("所有蓝图注册完成")
    except ImportError as e:
        logger.error(f"导入蓝图时出错: {str(e)}")
        raise

def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404错误: {request.path}")
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500错误: {str(error)}")
        return {'error': 'Internal server error'}, 500
    
    logger.debug("错误处理器注册完成")

# 注册主页路由
def register_main_routes(app):
    """注册主页路由和其他全局路由"""
    
    @app.route('/')
    def index():
        """主页路由 - 访问首页"""
        if current_user.is_authenticated:
            # 已登录用户重定向到设备页面或性能监控页面
            logger.debug("已认证用户访问首页，重定向到设备页面")
            return redirect(url_for('device.index'))
        else:
            # 未登录用户显示登录页面
            logger.debug("未认证用户访问首页，重定向到登录页面")
            return redirect(url_for('auth.login'))
    
    @app.route('/dashboard')
    def dashboard():
        """仪表板路由 - 显示系统概览"""
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        try:
            # 获取设备总数和状态统计
            from src.models import Device
            device_count = Device.query.count()
            normal_count = Device.query.filter_by(status='正常').count()
            maintenance_count = Device.query.filter_by(status='维修中').count()
            inactive_count = Device.query.filter_by(status='闲置').count()
            retired_count = Device.query.filter_by(status='报废').count()
            
            # 获取最近添加的设备，但避免使用created_at排序
            # 因为可能某些记录缺少此字段
            recent_devices = Device.query.order_by(Device.id.desc()).limit(5).all()
            
            # 安全处理，确保created_at存在
            for device in recent_devices:
                if not hasattr(device, 'created_at') or device.created_at is None:
                    device.created_at = None  # 确保模板能安全访问
            
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
            # 记录错误并返回错误页面
            import logging
            import traceback
            logging.error(f"仪表板加载错误: {str(e)}")
            logging.error(traceback.format_exc())
            return render_template('errors/500.html'), 500
    
    @app.route('/favicon.ico')
    def favicon():
        """提供网站图标"""
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    logger.debug("主页路由注册完成")

def create_tables_and_sample_data(app):
    """
    创建数据库表和样例数据
    
    Args:
        app: Flask应用实例
    """
    logger.debug("开始创建数据库表和样例数据...")
    with app.app_context():
        try:
            # 导入所需模型
            logger.debug("导入认证模型...")
            from src.modules.auth.models import User
            
            logger.debug("导入设备和性能模型...")
            from src.models import Device, DeviceType, PerformanceRecord, Threshold
            from src.models.device import init_device_types
            from src.core.db import db
            
            logger.info(f"正在使用数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].split('sqlite:///')[-1]
            logger.info(f"数据库文件路径: {db_path}")
            
            # 检查是否需要初始化数据库
            db_exists = os.path.exists(db_path) and os.path.getsize(db_path) > 0
            
            # 确保数据库表存在
            logger.debug("创建所有数据库表...")
            db.create_all()
            
            # 确保设备类型表存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.debug(f"当前数据库表: {tables}")
            
            if 'device_types' not in tables:
                logger.info("创建设备类型表...")
                db.create_all(tables=[DeviceType.__table__])
                logger.info("设备类型表创建成功")
                # 初始化设备类型
                init_device_types()
            
            if 'devices' not in tables:
                logger.info("创建设备表...")
                db.create_all(tables=[Device.__table__])
                logger.info("设备表创建成功")
            
            if 'performance_records' not in tables:
                logger.info("创建性能记录表...")
                db.create_all(tables=[PerformanceRecord.__table__])
                logger.info("性能记录表创建成功")
                
            if 'thresholds' not in tables:
                logger.info("创建阈值表...")
                db.create_all(tables=[Threshold.__table__])
                logger.info("阈值表创建成功")
            
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
            raise

# 如果直接运行此文件
if __name__ == '__main__':
    # 创建应用
    logger.info("直接运行app.py，开始创建应用...")
    app = create_app()
    
    # 创建数据库表和示例数据
    create_tables_and_sample_data(app)
    
    # 运行应用
    logger.info("启动Web服务...")
    app.run(debug=True, host='0.0.0.0') 