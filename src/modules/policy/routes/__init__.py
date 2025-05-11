#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略路由模块
导出策略管理相关的路由蓝图
"""

from src.modules.policy.routes.policy_routes import policy_bp, policy_template_bp
from src.modules.policy.routes.policy_view_routes import policy_view_bp

__all__ = ['policy_bp', 'policy_template_bp', 'policy_view_bp'] 