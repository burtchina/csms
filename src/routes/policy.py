from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from src.models.policy import Policy, PolicyTemplate, PolicyDeployment, PolicyAuditLog
from src.models.users import User
from src.models.devices import Device
from src.modules.policy.services.policy_service import PolicyService
from src.modules.policy.services.policy_template_service import PolicyTemplateService
from src.modules.policy.services.policy_deploy_service import PolicyDeployService
from sqlalchemy.exc import SQLAlchemyError
from src.core.auth import admin_required
from src.db import db
import json
from datetime import datetime

# 创建蓝图
policy_bp = Blueprint('policy', __name__, url_prefix='/policy')
policy_service = PolicyService()
template_service = PolicyTemplateService()
deploy_service = PolicyDeployService()

# 策略列表页面
@policy_bp.route('/')
@login_required
def index():
    """策略列表页面"""
    # 获取查询参数
    name = request.args.get('name', '')
    type = request.args.get('type', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 构建查询
    query = Policy.query
    
    # 应用过滤条件
    if name:
        query = query.filter(Policy.name.like(f'%{name}%'))
    if type:
        query = query.filter(Policy.type == type)
    if status:
        query = query.filter(Policy.status == status)
    
    # 获取分页结果
    pagination = query.order_by(Policy.created_at.desc()).paginate(page=page, per_page=per_page)
    policies = pagination.items
    
    return render_template('policy/index.html', policies=policies, pagination=pagination)

# 策略详情页面
@policy_bp.route('/<int:id>')
@login_required
def detail(id):
    """策略详情页面"""
    policy = Policy.query.get_or_404(id)
    deployments = PolicyDeployment.query.filter_by(policy_id=id).order_by(PolicyDeployment.deployed_at.desc()).all()
    audit_logs = PolicyAuditLog.query.filter_by(policy_id=id).order_by(PolicyAuditLog.created_at.desc()).all()
    
    return render_template('policy/detail.html', policy=policy, deployments=deployments, audit_logs=audit_logs)

# 新建策略页面
@policy_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """新建策略页面"""
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'description': request.form.get('description'),
                'config': json.loads(request.form.get('config', '{}')),
                'status': 'draft',
                'created_by': current_user.id
            }
            
            # 创建策略
            result = policy_service.create_policy(data, current_user.id)
            
            if result['success']:
                flash('策略创建成功', 'success')
                return redirect(url_for('policy.detail', id=result['policy_id']))
            else:
                flash(f'策略创建失败: {result["message"]}', 'danger')
        except Exception as e:
            flash(f'发生错误: {str(e)}', 'danger')
            db.session.rollback()
    
    # 获取模板列表
    templates = PolicyTemplate.query.all()
    
    return render_template('policy/edit.html', policy=None, templates=templates)

# 编辑策略页面
@policy_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """编辑策略页面"""
    policy = Policy.query.get_or_404(id)
    
    # 只有创建者或管理员可以编辑
    if policy.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此策略', 'danger')
        return redirect(url_for('policy.detail', id=id))
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'description': request.form.get('description'),
                'config': json.loads(request.form.get('config', '{}')),
                'status': request.form.get('status', 'draft')
            }
            
            # 更新策略
            result = policy_service.update_policy(id, data, current_user.id)
            
            if result['success']:
                flash('策略更新成功', 'success')
                return redirect(url_for('policy.detail', id=id))
            else:
                flash(f'策略更新失败: {result["message"]}', 'danger')
        except Exception as e:
            flash(f'发生错误: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('policy/edit.html', policy=policy)

# 删除策略
@policy_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除策略"""
    policy = Policy.query.get_or_404(id)
    
    # 只有创建者或管理员可以删除
    if policy.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此策略', 'danger')
        return redirect(url_for('policy.detail', id=id))
    
    try:
        # 删除策略（软删除）
        result = policy_service.delete_policy(id, current_user.id)
        
        if result['success']:
            flash('策略已删除', 'success')
            return redirect(url_for('policy.index'))
        else:
            flash(f'策略删除失败: {result["message"]}', 'danger')
            return redirect(url_for('policy.detail', id=id))
    except Exception as e:
        flash(f'发生错误: {str(e)}', 'danger')
        db.session.rollback()
        return redirect(url_for('policy.detail', id=id))

# 策略部署页面
@policy_bp.route('/<int:id>/deploy', methods=['GET', 'POST'])
@login_required
def deploy(id):
    """策略部署页面"""
    policy = Policy.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            device_ids = request.form.getlist('device_ids')
            
            if not device_ids:
                flash('请选择至少一个设备进行部署', 'warning')
                return redirect(url_for('policy.deploy', id=id))
            
            # 部署策略
            result = deploy_service.deploy_policy(id, device_ids, current_user.id)
            
            if result['success']:
                flash('策略部署任务已提交，请查看部署状态', 'success')
                return redirect(url_for('policy.detail', id=id))
            else:
                flash(f'策略部署失败: {result["message"]}', 'danger')
        except Exception as e:
            flash(f'发生错误: {str(e)}', 'danger')
            db.session.rollback()
    
    # 获取可用设备列表
    devices = Device.query.filter_by(status='active').all()
    
    # 获取已部署设备列表
    deployed_devices = db.session.query(Device.id).join(
        PolicyDeployment, PolicyDeployment.device_id == Device.id
    ).filter(
        PolicyDeployment.policy_id == id,
        PolicyDeployment.status == 'success'
    ).all()
    
    deployed_device_ids = [d.id for d in deployed_devices]
    
    return render_template('policy/deploy.html', policy=policy, devices=devices, deployed_device_ids=deployed_device_ids)

# 策略回滚
@policy_bp.route('/deployment/<int:id>/rollback', methods=['POST'])
@login_required
def rollback(id):
    """回滚策略部署"""
    deployment = PolicyDeployment.query.get_or_404(id)
    
    try:
        # 回滚策略
        result = deploy_service.rollback_deployment(id, current_user.id)
        
        if result['success']:
            flash('策略回滚成功', 'success')
        else:
            flash(f'策略回滚失败: {result["message"]}', 'danger')
    except Exception as e:
        flash(f'发生错误: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('policy.detail', id=deployment.policy_id))

# 验证策略配置
@policy_bp.route('/validate', methods=['POST'])
@login_required
def validate():
    """验证策略配置API"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'errors': ['请提供配置数据']})
        
        # 调用策略验证服务
        result = policy_service.validate_policy_config(data.get('type'), data.get('config'))
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]})

# 模板管理页面
@policy_bp.route('/templates')
@login_required
def templates():
    """模板列表页面"""
    system_templates = PolicyTemplate.query.filter_by(is_system=True).all()
    user_templates = PolicyTemplate.query.filter_by(is_system=False).all()
    
    return render_template('policy/templates.html', system_templates=system_templates, user_templates=user_templates)

# 获取模板详情API
@policy_bp.route('/templates/<int:id>', methods=['GET'])
@login_required
def get_template(id):
    """获取模板详情API"""
    try:
        template = PolicyTemplate.query.get_or_404(id)
        
        # 构建模板数据
        template_data = {
            'id': template.id,
            'name': template.name,
            'type': template.type,
            'description': template.description,
            'config': template.config,
            'is_system': template.is_system
        }
        
        return jsonify({'success': True, 'template': template_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 创建模板
@policy_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """创建模板页面"""
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'description': request.form.get('description'),
                'config': json.loads(request.form.get('config', '{}')),
                'is_system': False,
                'created_by': current_user.id
            }
            
            # 创建模板
            result = template_service.create_template(data, current_user.id)
            
            if result['success']:
                flash('模板创建成功', 'success')
                return redirect(url_for('policy.templates'))
            else:
                flash(f'模板创建失败: {result["message"]}', 'danger')
        except Exception as e:
            flash(f'发生错误: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('policy/edit_template.html', template=None)

# 编辑模板
@policy_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(id):
    """编辑模板页面"""
    template = PolicyTemplate.query.get_or_404(id)
    
    # 系统模板只有管理员可以编辑
    if template.is_system and not current_user.is_admin:
        flash('您没有权限编辑系统模板', 'danger')
        return redirect(url_for('policy.templates'))
    
    # 用户模板只有创建者或管理员可以编辑
    if not template.is_system and template.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限编辑此模板', 'danger')
        return redirect(url_for('policy.templates'))
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'description': request.form.get('description'),
                'config': json.loads(request.form.get('config', '{}'))
            }
            
            # 更新模板
            result = template_service.update_template(id, data)
            
            if result['success']:
                flash('模板更新成功', 'success')
                return redirect(url_for('policy.templates'))
            else:
                flash(f'模板更新失败: {result["message"]}', 'danger')
        except Exception as e:
            flash(f'发生错误: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('policy/edit_template.html', template=template)

# 删除模板
@policy_bp.route('/templates/<int:id>/delete', methods=['POST'])
@login_required
def delete_template(id):
    """删除模板"""
    template = PolicyTemplate.query.get_or_404(id)
    
    # 系统模板只有管理员可以删除
    if template.is_system and not current_user.is_admin:
        flash('您没有权限删除系统模板', 'danger')
        return redirect(url_for('policy.templates'))
    
    # 用户模板只有创建者或管理员可以删除
    if not template.is_system and template.created_by != current_user.id and not current_user.is_admin:
        flash('您没有权限删除此模板', 'danger')
        return redirect(url_for('policy.templates'))
    
    try:
        # 删除模板
        result = template_service.delete_template(id)
        
        if result['success']:
            flash('模板已删除', 'success')
        else:
            flash(f'模板删除失败: {result["message"]}', 'danger')
    except Exception as e:
        flash(f'发生错误: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('policy.templates')) 