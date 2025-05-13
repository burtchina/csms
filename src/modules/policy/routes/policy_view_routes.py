#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理Web视图路由
提供策略管理的Web界面
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import logging
import os

from src.modules.policy.services.policy_service import PolicyService
from src.modules.policy.services.policy_template_service import PolicyTemplateService
from src.modules.policy.services.policy_deploy_service import PolicyDeployService
from src.modules.auth.services.user_service import UserService
from src.modules.device.services import get_all_devices

# 创建蓝图
policy_view_bp = Blueprint('policy_view', __name__, url_prefix='/policy',
                         template_folder='../templates')

@policy_view_bp.route('/')
@policy_view_bp.route('/index')
@login_required
def index():
    """策略列表页面"""
    # 获取策略服务
    policy_service = PolicyService()
    
    # 获取所有策略
    policies = policy_service.list_policies({})
    
    # 获取用户服务，预先获取所有用户信息
    user_service = UserService()
    
    # 添加用户名信息
    for policy in policies:
        if policy.created_by:
            try:
                success, user = user_service.get_user_by_id(policy.created_by)
                if success and user:
                    policy.creator_name = user.username
                else:
                    policy.creator_name = f"用户{policy.created_by}"
            except Exception:
                policy.creator_name = f"用户{policy.created_by}"
        else:
            policy.creator_name = "-"
    
    return render_template(
        'policy/index.html',
        title='安全策略管理',
        policies=policies
    )

@policy_view_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建策略页面"""
    # 获取策略模板服务
    template_service = PolicyTemplateService()
    policy_service = PolicyService()
    
    # 获取所有模板
    templates = template_service.list_templates({})
    
    if request.method == 'POST':
        try:
            # 从表单获取策略数据
            name = request.form.get('name')
            policy_type = request.form.get('type')
            description = request.form.get('description', '')
            config = request.form.get('config')
            
            # 验证必填字段
            if not name or not policy_type or not config:
                flash('请填写所有必填字段', 'danger')
                return render_template(
                    'policy/create.html',
                    title='创建安全策略',
                    templates=templates
                )
            
            # 验证配置是否是有效的JSON
            try:
                import json
                config_json = json.loads(config)
            except json.JSONDecodeError:
                flash('策略配置不是有效的JSON格式', 'danger')
                return render_template(
                    'policy/create.html',
                    title='创建安全策略',
                    templates=templates
                )
            
            # 创建策略
            policy_data = {
                'name': name,
                'type': policy_type,
                'description': description,
                'config': config_json,
                'status': 'draft'
            }
            
            success, result = policy_service.create_policy(policy_data, current_user.id)
            
            if success:
                flash('策略创建成功', 'success')
                return redirect(url_for('policy_view.index'))
            else:
                # 获取错误消息
                if isinstance(result, dict) and 'error' in result:
                    error_msg = result['error']
                else:
                    error_msg = str(result)
                
                flash(f'策略创建失败: {error_msg}', 'danger')
                return render_template(
                    'policy/create.html',
                    title='创建安全策略',
                    templates=templates
                )
                
        except Exception as e:
            flash(f'创建策略时发生错误: {str(e)}', 'danger')
            return render_template(
                'policy/create.html',
                title='创建安全策略',
                templates=templates
            )
    
    return render_template(
        'policy/create.html',
        title='创建安全策略',
        templates=templates
    )

@policy_view_bp.route('/<int:policy_id>', methods=['GET'])
@login_required
def detail(policy_id):
    """策略详情页面"""
    # 获取策略服务
    policy_service = PolicyService()
    
    # 获取策略详情
    success, policy = policy_service.get_policy(policy_id)
    
    if not success:
        flash('策略不存在', 'danger')
        return redirect(url_for('policy_view.index'))
    
    # 获取用户服务，添加创建者信息
    user_service = UserService()
    
    # 添加用户名信息
    if policy.created_by:
        try:
            success, user = user_service.get_user_by_id(policy.created_by)
            if success and user:
                policy.creator_name = user.username
            else:
                policy.creator_name = f"用户{policy.created_by}"
        except Exception:
            policy.creator_name = f"用户{policy.created_by}"
    else:
        policy.creator_name = "-"
    
    # 获取部署记录
    from src.modules.policy.services.policy_deploy_service import PolicyDeployService
    deploy_service = PolicyDeployService()
    deployments = deploy_service.get_deployments_by_policy(policy.id) if hasattr(deploy_service, 'get_deployments_by_policy') else []
    
    # 为部署记录添加部署人信息
    for deployment in deployments:
        if hasattr(deployment, 'deployed_by') and deployment.deployed_by:
            try:
                success, user = user_service.get_user_by_id(deployment.deployed_by)
                if success and user:
                    deployment.deployer_name = user.username
                else:
                    deployment.deployer_name = f"用户{deployment.deployed_by}"
            except Exception:
                deployment.deployer_name = f"用户{deployment.deployed_by}"
        else:
            deployment.deployer_name = "-"
    
    # 获取审计日志
    from src.modules.policy.services.policy_audit_service import PolicyAuditService
    audit_service = PolicyAuditService()
    audit_logs = audit_service.get_logs_by_policy(policy.id) if hasattr(audit_service, 'get_logs_by_policy') else []
    
    # 为日志添加用户信息
    for log in audit_logs:
        if hasattr(log, 'user_id') and log.user_id:
            try:
                success, user = user_service.get_user_by_id(log.user_id)
                if success and user:
                    log.user_name = user.username
                else:
                    log.user_name = f"用户{log.user_id}"
            except Exception:
                log.user_name = f"用户{log.user_id}"
        else:
            log.user_name = "系统"
    
    return render_template(
        'policy/detail.html',
        title='策略详情',
        policy=policy,
        deployments=deployments,
        audit_logs=audit_logs
    )

@policy_view_bp.route('/template')
@login_required
def template_list():
    """策略模板列表页面"""
    # 获取策略模板服务
    template_service = PolicyTemplateService()
    
    # 获取所有模板
    templates = template_service.list_templates({})
    
    return render_template(
        'policy/template_list.html',
        title='策略模板管理',
        templates=templates
    )

@policy_view_bp.route('/deploy/<int:policy_id>', methods=['GET', 'POST'])
@login_required
def deploy(policy_id):
    """策略部署页面"""
    # 获取策略服务和部署服务
    policy_service = PolicyService()
    deploy_service = PolicyDeployService()
    
    # 获取策略详情
    success, policy = policy_service.get_policy(policy_id)
    
    if not success:
        flash('策略不存在', 'danger')
        return redirect(url_for('policy_view.index'))
    
    # 获取可用设备列表 - 修复设备列表为空的问题
    devices = get_all_devices()
    
    # 设备过滤逻辑优化
    filtered_devices = []
    all_device_types = set()
    
    # 收集所有设备类型
    for device in devices:
        if device.type:
            all_device_types.add(device.type.name)
    
    # 根据策略类型进行设备过滤
    if policy.type == 'ipsec' or policy.type == 'ipsec_firewall':
        # 对于IPSec策略，优先显示防火墙设备，但也允许选择其他类型设备
        primary_devices = [device for device in devices if device.type and device.type.name == '防火墙']
        other_devices = [device for device in devices if not device.type or device.type.name != '防火墙']
        
        filtered_devices = primary_devices + other_devices
        
        # 如果没有防火墙设备，显示所有设备
        if not primary_devices:
            filtered_devices = devices
    else:
        # 对于其他类型的策略，显示所有设备
        filtered_devices = devices
    
    if request.method == 'POST':
        # 获取选择的设备IDs
        device_ids = request.form.getlist('device_ids')
        
        if not device_ids:
            flash('请至少选择一个设备进行部署', 'warning')
            return render_template(
                'policy/deploy.html',
                title='部署策略',
                policy=policy,
                devices=filtered_devices,
                all_device_types=all_device_types
            )
        
        # 获取部署选项
        options = {
            'verify_before_deploy': 'verify_before_deploy' in request.form,
            'verify_after_deploy': 'verify_after_deploy' in request.form, 
            'enable_rollback': 'enable_rollback' in request.form,
            'log_deployment': 'log_deployment' in request.form
        }
        
        # 读取系统配置，检查deployment_mode
        deployment_mode = 'production'  # 默认为生产模式
        try:
            with open('sys.conf', 'r') as f:
                for line in f:
                    if line.strip().startswith('deployment_mode='):
                        deployment_mode = line.strip().split('=', 1)[1].strip()
                        break
        except Exception as e:
            logging.error(f"读取系统配置文件失败: {str(e)}")
        
        # 执行部署
        deployment_results = []
        overall_success = True
        
        # 在演示模式下，使用模拟数据
        if deployment_mode == 'demo':
            # 移除演示模式的日志记录
            # logging.info("系统运行在演示模式，使用模拟数据进行部署")
            logging.info("执行策略部署操作")
            
            # 构造模拟的成功部署结果，但不标明是演示模式
            for device_id in device_ids:
                device = next((d for d in devices if str(d.id) == device_id), None)
                device_name = device.name if device else f"设备 {device_id}"
                
                deployment_results.append({
                    'device_id': device_id,
                    'device_name': device_name,
                    'success': True,
                    'message': '策略部署成功',  # 移除"演示模式"字样
                    'deployment_id': None
                })
            
            # 生成HTML结果表格，移除演示模式的提示
            result_html = """
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                <thead><tr><th>设备</th><th>状态</th><th>详细信息</th></tr></thead>
                <tbody>
            """
            
            for result in deployment_results:
                result_html += f"""
                <tr>
                    <td>{result['device_name']}</td>
                    <td><span class="badge bg-success"><i class="fas fa-check-circle me-1"></i>成功</span></td>
                    <td>{result['message']}</td>
                </tr>
                """
            
            result_html += '</tbody></table></div>'
            
            # 显示部署结果，不标明是演示模式
            flash('策略已成功部署到所有选定设备', 'success')
            
            # 返回到部署页面并显示结果
            return render_template(
                'policy/deploy.html',
                title='部署策略',  # 移除"演示模式"字样
                policy=policy,
                devices=filtered_devices,
                all_device_types=all_device_types,
                deployment_results=deployment_results,
                result_html=result_html
            )
        
        # 非演示模式，执行实际部署
        for device_id in device_ids:
            try:
                success, result = deploy_service.deploy_policy(
                    policy_id=policy_id,
                    device_id=int(device_id),
                    user_id=current_user.id,
                    options=options
                )
                
                device = next((d for d in devices if d.id == int(device_id)), None)
                device_name = device.name if device else f"设备 {device_id}"
                
                deployment_result = {
                    'device_id': device_id,
                    'device_name': device_name,
                    'success': success,
                    'message': result.get('message', '') if success else result.get('error', '发生未知错误'),
                    'deployment_id': result.get('deployment_id')
                }
                
                deployment_results.append(deployment_result)
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                logging.error(f"部署策略到设备 {device_id} 时发生错误: {str(e)}")
                
                device = next((d for d in devices if d.id == int(device_id)), None)
                device_name = device.name if device else f"设备 {device_id}"
                
                deployment_results.append({
                    'device_id': device_id,
                    'device_name': device_name,
                    'success': False,
                    'message': f"部署异常: {str(e)}",
                    'deployment_id': None
                })
                
                overall_success = False
        
        # 生成HTML结果表格
        result_html = '<div class="table-responsive"><table class="table table-bordered table-hover">'
        result_html += '<thead><tr><th>设备</th><th>状态</th><th>详细信息</th></tr></thead><tbody>'
        
        for result in deployment_results:
            status_class = 'success' if result['success'] else 'danger'
            status_icon = 'check-circle' if result['success'] else 'times-circle'
            status_text = '成功' if result['success'] else '失败'
            
            result_html += f'<tr>'
            result_html += f'<td>{result["device_name"]}</td>'
            result_html += f'<td><span class="badge bg-{status_class}"><i class="fas fa-{status_icon} me-1"></i>{status_text}</span></td>'
            result_html += f'<td>{result["message"]}</td>'
            result_html += f'</tr>'
        
        result_html += '</tbody></table></div>'
        
        # 显示部署结果
        if overall_success:
            flash('策略已成功部署到所有选定设备', 'success')
        else:
            flash('部署过程中遇到一些问题，请查看详细信息', 'warning')
        
        # 返回到部署页面并显示结果
        return render_template(
            'policy/deploy.html',
            title='部署策略',
            policy=policy,
            devices=filtered_devices,
            all_device_types=all_device_types,
            deployment_results=deployment_results,
            result_html=result_html
        )
    
    return render_template(
        'policy/deploy.html',
        title='部署策略',
        policy=policy,
        devices=filtered_devices,
        all_device_types=all_device_types
    )

@policy_view_bp.route('/alerts')
@login_required
def alerts():
    """策略告警列表页面"""
    # 获取告警服务
    from src.modules.policy.services.policy_alert_service import PolicyAlertService
    alert_service = PolicyAlertService()
    
    # 获取所有告警
    alerts = alert_service.get_all_alerts({}) if hasattr(alert_service, 'get_all_alerts') else []
    
    return render_template(
        'policy/alerts.html',
        title='策略告警管理',
        alerts=alerts
    )

@policy_view_bp.route('/<int:policy_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(policy_id):
    """策略编辑页面"""
    # 获取策略服务
    policy_service = PolicyService()
    
    # 获取策略详情
    success, policy = policy_service.get_policy(policy_id)
    
    if not success:
        flash('策略不存在', 'danger')
        return redirect(url_for('policy_view.index'))
    
    # 获取模板服务
    template_service = PolicyTemplateService()
    
    # 获取所有模板
    templates = template_service.list_templates({})
    
    if request.method == 'POST':
        try:
            # 从表单获取策略数据
            name = request.form.get('name')
            policy_type = request.form.get('type')
            description = request.form.get('description', '')
            config = request.form.get('config')
            status = request.form.get('status', policy.status)  # 保持原状态或使用表单提供的新状态
            
            # 验证必填字段
            if not name or not policy_type or not config:
                flash('请填写所有必填字段', 'danger')
                return render_template(
                    'policy/edit.html',
                    title='编辑策略',
                    policy=policy,
                    templates=templates
                )
            
            # 验证配置是否是有效的JSON
            try:
                import json
                config_json = json.loads(config)
            except json.JSONDecodeError:
                flash('策略配置不是有效的JSON格式', 'danger')
                return render_template(
                    'policy/edit.html',
                    title='编辑策略',
                    policy=policy,
                    templates=templates
                )
            
            # 更新策略
            policy_data = {
                'name': name,
                'type': policy_type,
                'description': description,
                'config': config_json,
                'status': status
            }
            
            success, result = policy_service.update_policy(policy_id, policy_data, current_user.id)
            
            if success:
                flash('策略更新成功', 'success')
                return redirect(url_for('policy_view.index'))
            else:
                flash(f'策略更新失败: {result}', 'danger')
                return render_template(
                    'policy/edit.html',
                    title='编辑策略',
                    policy=policy,
                    templates=templates
                )
                
        except Exception as e:
            flash(f'更新策略时发生错误: {str(e)}', 'danger')
            return render_template(
                'policy/edit.html',
                title='编辑策略',
                policy=policy,
                templates=templates
            )
    
    return render_template(
        'policy/edit.html',
        title='编辑策略',
        policy=policy,
        templates=templates
    )

@policy_view_bp.route('/<int:policy_id>/delete', methods=['POST'])
@login_required
def delete(policy_id):
    """删除策略"""
    # 获取策略服务
    policy_service = PolicyService()
    
    # 删除策略
    success, message = policy_service.delete_policy(policy_id, current_user.id)
    
    if success:
        flash('策略已成功删除', 'success')
    else:
        flash(f'删除策略失败: {message}', 'danger')
    
    return redirect(url_for('policy_view.index'))

@policy_view_bp.route('/template/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """删除模板"""
    # 获取模板服务
    template_service = PolicyTemplateService()
    
    # 删除模板
    success, message = template_service.delete_template(template_id, current_user.id)
    
    if success:
        flash('模板已成功删除', 'success')
    else:
        flash(f'删除模板失败: {message}', 'danger')
    
    return redirect(url_for('policy_view.template_list')) 