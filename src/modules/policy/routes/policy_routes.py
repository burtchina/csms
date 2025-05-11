#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理API路由
提供策略相关的RESTful API接口
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.modules.policy.services.policy_service import PolicyService
from src.modules.policy.services.policy_template_service import PolicyTemplateService
from src.modules.auth.services.permission_service import require_permission


# 创建蓝图
policy_bp = Blueprint('policy', __name__, url_prefix='/api/policies')
policy_template_bp = Blueprint('policy_template', __name__, url_prefix='/api/policy-templates')


@policy_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('policy:view')
def list_policies():
    """获取策略列表"""
    filters = {}
    
    # 解析查询参数
    if request.args.get('name'):
        filters['name'] = request.args.get('name')
    
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    # 获取策略列表
    policy_service = PolicyService()
    policies = policy_service.list_policies(filters)
    
    # 转换为字典列表
    result = [policy.to_dict() for policy in policies]
    
    return jsonify({
        'status': 'success',
        'data': result
    }), 200


@policy_bp.route('/<int:policy_id>', methods=['GET'])
@jwt_required()
@require_permission('policy:view')
def get_policy(policy_id):
    """获取策略详情"""
    policy_service = PolicyService()
    success, result = policy_service.get_policy(policy_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '获取策略失败')
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': result.to_dict()
    }), 200


@policy_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('policy:create')
def create_policy():
    """创建策略"""
    # 获取请求数据
    policy_data = request.json
    if not policy_data:
        return jsonify({
            'status': 'error',
            'message': '缺少请求数据'
        }), 400
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 创建策略
    policy_service = PolicyService()
    success, result = policy_service.create_policy(policy_data, user_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '创建策略失败')
        }), 400
    
    return jsonify({
        'status': 'success',
        'message': '策略创建成功',
        'data': result.to_dict()
    }), 201


@policy_bp.route('/<int:policy_id>', methods=['PUT'])
@jwt_required()
@require_permission('policy:edit')
def update_policy(policy_id):
    """更新策略"""
    # 获取请求数据
    policy_data = request.json
    if not policy_data:
        return jsonify({
            'status': 'error',
            'message': '缺少请求数据'
        }), 400
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 更新策略
    policy_service = PolicyService()
    success, result = policy_service.update_policy(policy_id, policy_data, user_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '更新策略失败')
        }), 400
    
    return jsonify({
        'status': 'success',
        'message': '策略更新成功',
        'data': result.to_dict()
    }), 200


@policy_bp.route('/<int:policy_id>', methods=['DELETE'])
@jwt_required()
@require_permission('policy:delete')
def delete_policy(policy_id):
    """删除策略"""
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 删除策略
    policy_service = PolicyService()
    success, result = policy_service.delete_policy(policy_id, user_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '删除策略失败')
        }), 400
    
    return jsonify({
        'status': 'success',
        'message': '策略删除成功'
    }), 200


# 策略模板路由
@policy_template_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('policy:view')
def list_templates():
    """获取策略模板列表"""
    filters = {}
    
    # 解析查询参数
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    
    if request.args.get('is_system') is not None:
        filters['is_system'] = request.args.get('is_system').lower() == 'true'
    
    # 获取模板列表
    template_service = PolicyTemplateService()
    templates = template_service.list_templates(filters)
    
    # 转换为字典列表
    result = []
    for template in templates:
        template_dict = {
            'id': template.id,
            'name': template.name,
            'type': template.type,
            'description': template.description,
            'config': template.config,
            'is_system': template.is_system,
            'created_by': template.created_by,
            'created_at': template.created_at.isoformat() if template.created_at else None
        }
        result.append(template_dict)
    
    return jsonify({
        'status': 'success',
        'data': result
    }), 200


@policy_template_bp.route('/<int:template_id>', methods=['GET'])
@jwt_required()
@require_permission('policy:view')
def get_template(template_id):
    """获取策略模板详情"""
    template_service = PolicyTemplateService()
    success, result = template_service.get_template(template_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '获取模板失败')
        }), 404
    
    template_dict = {
        'id': result.id,
        'name': result.name,
        'type': result.type,
        'description': result.description,
        'config': result.config,
        'is_system': result.is_system,
        'created_by': result.created_by,
        'created_at': result.created_at.isoformat() if result.created_at else None
    }
    
    return jsonify({
        'status': 'success',
        'data': template_dict
    }), 200


@policy_template_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('policy:create')
def create_template():
    """创建策略模板"""
    # 获取请求数据
    template_data = request.json
    if not template_data:
        return jsonify({
            'status': 'error',
            'message': '缺少请求数据'
        }), 400
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 创建模板
    template_service = PolicyTemplateService()
    success, result = template_service.create_template(template_data, user_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '创建模板失败')
        }), 400
    
    template_dict = {
        'id': result.id,
        'name': result.name,
        'type': result.type,
        'description': result.description,
        'config': result.config,
        'is_system': result.is_system,
        'created_by': result.created_by,
        'created_at': result.created_at.isoformat() if result.created_at else None
    }
    
    return jsonify({
        'status': 'success',
        'message': '模板创建成功',
        'data': template_dict
    }), 201


@policy_template_bp.route('/<int:template_id>', methods=['PUT'])
@jwt_required()
@require_permission('policy:edit')
def update_template(template_id):
    """更新策略模板"""
    # 获取请求数据
    template_data = request.json
    if not template_data:
        return jsonify({
            'status': 'error',
            'message': '缺少请求数据'
        }), 400
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 更新模板
    template_service = PolicyTemplateService()
    success, result = template_service.update_template(template_id, template_data, user_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '更新模板失败')
        }), 400
    
    template_dict = {
        'id': result.id,
        'name': result.name,
        'type': result.type,
        'description': result.description,
        'config': result.config,
        'is_system': result.is_system,
        'created_by': result.created_by,
        'created_at': result.created_at.isoformat() if result.created_at else None
    }
    
    return jsonify({
        'status': 'success',
        'message': '模板更新成功',
        'data': template_dict
    }), 200


@policy_template_bp.route('/<int:template_id>', methods=['DELETE'])
@jwt_required()
@require_permission('policy:delete')
def delete_template(template_id):
    """删除策略模板"""
    # 删除模板
    template_service = PolicyTemplateService()
    success, result = template_service.delete_template(template_id)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': result.get('error', '删除模板失败')
        }), 400
    
    return jsonify({
        'status': 'success',
        'message': '模板删除成功'
    }), 200


@policy_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_policy_config():
    """验证策略配置"""
    # 获取请求数据
    data = request.json
    if not data:
        return jsonify({
            'status': 'error',
            'message': '缺少请求数据'
        }), 400
    
    policy_type = data.get('type')
    config = data.get('config')
    
    if not policy_type or not config:
        return jsonify({
            'status': 'error',
            'message': '请提供策略类型和配置'
        }), 400
    
    # 验证策略配置
    policy_service = PolicyService()
    result = policy_service.validate_policy_config(policy_type, config)
    
    if result.get('success'):
        return jsonify({
            'status': 'success',
            'message': '策略配置有效'
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': '策略配置无效',
            'errors': result.get('errors', [])
        }), 400 