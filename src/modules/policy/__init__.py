#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理模块
实现IPSec与防火墙联动策略管理功能
"""

from src.modules.policy.routes import policy_bp, policy_template_bp, policy_view_bp
from src.modules.policy.routes.policy_deploy_routes import policy_deploy_bp
from src.modules.policy.services.policy_sync_scheduler import get_scheduler

# 全局标记防止重复创建模板目录
_template_directory_ensured = False

def init_app(app):
    """初始化策略管理模块
    
    Args:
        app: Flask应用实例
    """
    # 注册路由蓝图
    app.register_blueprint(policy_bp)
    app.register_blueprint(policy_template_bp)
    app.register_blueprint(policy_deploy_bp)
    app.register_blueprint(policy_view_bp)
    
    # 创建策略模板目录(仅需执行一次)
    global _template_directory_ensured
    if not _template_directory_ensured:
        from src.modules.policy.templates import ensure_template_directory
        ensure_template_directory()
        _template_directory_ensured = True
        app.logger.info("策略模板目录检查完成")
    
    # 使用应用启动后事件启动调度器
    # Flask 2.x版本使用app.before_first_request已被废弃
    @app.before_request
    def ensure_scheduler_running():
        from flask import g
        if not hasattr(g, 'scheduler_started'):
            with app.app_context():
                scheduler = get_scheduler()
                if scheduler.enabled and not scheduler.running:
                    scheduler.start()
            g.scheduler_started = True

__all__ = ['init_app', 'policy_view_bp', 'policy_template_bp', 'policy_deploy_bp'] 