#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略下发API路由模块
提供策略下发、回滚、状态查询等RESTful API
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.modules.policy.services.policy_deploy_service import PolicyDeployService
from src.modules.policy.services.policy_sync_scheduler import get_scheduler

# 创建蓝图
policy_deploy_bp = Blueprint('policy_deploy', __name__, url_prefix='/api/policy-deploy')

# 策略下发服务实例
deploy_service = PolicyDeployService()


@policy_deploy_bp.route('/deploy', methods=['POST'])
@login_required
def deploy_policy():
    """部署策略API
    
    请求参数：
        - policy_id: 策略ID
        - device_id: 设备ID
        
    返回：
        - 部署结果
    """
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        device_id = data.get('device_id')
        
        if not policy_id or not device_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数',
                'data': None
            }), 400
        
        success, result = deploy_service.deploy_policy(
            policy_id=int(policy_id),
            device_id=int(device_id),
            user_id=current_user.id
        )
        
        return jsonify({
            'success': success,
            'message': result.get('message', ''),
            'error': result.get('error', ''),
            'data': result
        }), 200 if success else 400
        
    except Exception as e:
        logging.error(f"部署策略时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/rollback', methods=['POST'])
@login_required
def rollback_policy():
    """回滚策略API
    
    请求参数：
        - policy_id: 策略ID
        - device_id: 设备ID
        
    返回：
        - 回滚结果
    """
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        device_id = data.get('device_id')
        
        if not policy_id or not device_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数',
                'data': None
            }), 400
        
        success, result = deploy_service.rollback_policy(
            policy_id=int(policy_id),
            device_id=int(device_id),
            user_id=current_user.id
        )
        
        return jsonify({
            'success': success,
            'message': result.get('message', ''),
            'error': result.get('error', ''),
            'data': result
        }), 200 if success else 400
        
    except Exception as e:
        logging.error(f"回滚策略时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/status', methods=['GET'])
@login_required
def get_policy_status():
    """获取策略状态API
    
    URL参数：
        - policy_id: 策略ID
        - device_id: 设备ID
        
    返回：
        - 策略状态信息
    """
    try:
        policy_id = request.args.get('policy_id')
        device_id = request.args.get('device_id')
        
        if not policy_id or not device_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数',
                'data': None
            }), 400
        
        success, result = deploy_service.get_policy_status(
            policy_id=int(policy_id),
            device_id=int(device_id)
        )
        
        return jsonify({
            'success': success,
            'message': '',
            'error': result.get('error', ''),
            'data': result
        }), 200 if success else 400
        
    except Exception as e:
        logging.error(f"获取策略状态时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/verify', methods=['POST'])
@login_required
def verify_policy():
    """验证策略API
    
    请求参数：
        - policy_id: 策略ID
        - device_id: 设备ID
        
    返回：
        - 验证结果
    """
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        device_id = data.get('device_id')
        
        if not policy_id or not device_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数',
                'data': None
            }), 400
        
        success, result = deploy_service.verify_policy(
            policy_id=int(policy_id),
            device_id=int(device_id)
        )
        
        return jsonify({
            'success': success,
            'message': result.get('message', ''),
            'error': result.get('error', ''),
            'data': result
        }), 200 if success else 400
        
    except Exception as e:
        logging.error(f"验证策略时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/sync', methods=['POST'])
@login_required
def sync_policies():
    """同步策略状态API
    
    请求参数（可选）：
        - policy_id: 特定策略ID
        - device_id: 特定设备ID
        
    返回：
        - 同步结果统计
    """
    try:
        data = request.get_json() or {}
        policy_id = data.get('policy_id')
        device_id = data.get('device_id')
        
        # 手动触发同步
        result = deploy_service.sync_policy_status(
            policy_id=int(policy_id) if policy_id else None,
            device_id=int(device_id) if device_id else None
        )
        
        return jsonify({
            'success': True,
            'message': '策略同步已完成',
            'data': result
        }), 200
        
    except Exception as e:
        logging.error(f"同步策略时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/sync/config', methods=['POST'])
@login_required
def config_sync_scheduler():
    """配置策略同步调度器API
    
    请求参数：
        - enabled: 是否启用调度器
        - interval: 同步间隔（秒）
        - alert_on_failure: 是否在同步失败时发送告警
        - alert_threshold: 连续失败多少次后发送告警
        
    返回：
        - 配置结果
    """
    try:
        # 检查权限（仅管理员可以配置调度器）
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': '权限不足',
                'data': None
            }), 403
        
        data = request.get_json()
        scheduler = get_scheduler()
        
        # 更新配置
        scheduler.set_config(data)
        
        # 返回当前状态
        return jsonify({
            'success': True,
            'message': '同步调度器配置已更新',
            'data': scheduler.get_status()
        }), 200
        
    except Exception as e:
        logging.error(f"配置策略同步调度器时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500


@policy_deploy_bp.route('/sync/status', methods=['GET'])
@login_required
def get_sync_status():
    """获取策略同步调度器状态API
    
    返回：
        - 调度器状态信息
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        return jsonify({
            'success': True,
            'message': '',
            'data': status
        }), 200
        
    except Exception as e:
        logging.error(f"获取策略同步调度器状态时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'error': str(e),
            'data': None
        }), 500 