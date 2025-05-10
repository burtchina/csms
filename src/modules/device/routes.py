#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备管理相关路由
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from src.db import db
from src.models.device import Device, DeviceType
from src.modules.device import device_bp
from src.modules.device.services import (
    get_all_devices, 
    get_device_by_id, 
    test_device_connection,
    get_device_info
)

# 设备列表
@device_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 搜索和筛选
    search_query = request.args.get('search', '')
    device_type = request.args.get('type', '')
    status = request.args.get('status', '')
    
    query = Device.query
    
    # 应用搜索条件
    if search_query:
        query = query.filter(
            (Device.name.like(f'%{search_query}%')) |
            (Device.device_code.like(f'%{search_query}%')) |
            (Device.location.like(f'%{search_query}%'))
        )
    
    # 应用类型筛选
    if device_type:
        query = query.filter(Device.type_id == device_type)
    
    # 应用状态筛选
    if status:
        query = query.filter(Device.status == status)
    
    # 确保加载设备类型信息 - 使用joinedload预加载关联的设备类型
    query = query.options(joinedload(Device.type))
    
    # 分页查询
    pagination = query.order_by(desc(Device.updated_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    devices = pagination.items
    
    # 获取所有设备类型，用于筛选
    device_types = DeviceType.query.all()
    
    # 获取所有可能的状态值，用于筛选
    status_options = db.session.query(Device.status).distinct().all()
    status_options = [status[0] for status in status_options if status[0]]  # 过滤掉空值
    
    # 如果没有状态选项，添加默认状态
    if not status_options:
        status_options = ['正常', '维修中', '闲置', '报废']
    
    return render_template(
        'device/index.html',
        devices=devices,
        pagination=pagination,
        device_types=device_types,
        status_options=status_options,
        search_query=search_query,
        selected_type=device_type,
        selected_status=status
    )

# 添加设备
@device_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # 获取所有设备类型
    device_types = DeviceType.query.all()
    
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        device_code = request.form.get('device_code')
        type_id = request.form.get('type_id')
        location = request.form.get('location')
        ip_address = request.form.get('ip_address')
        mac_address = request.form.get('mac_address')
        username = request.form.get('username')
        password = request.form.get('password')
        status = request.form.get('status')
        manufacturer = request.form.get('manufacturer')
        model = request.form.get('model')
        serial_number = request.form.get('serial_number')
        
        # 日期处理
        purchase_date = None
        if request.form.get('purchase_date'):
            try:
                purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('购买日期格式不正确', 'danger')
                return render_template('device/add.html', device_types=device_types)
        
        warranty_period = request.form.get('warranty_period')
        notes = request.form.get('notes')
        
        # 验证必填字段
        if not name or not device_code:
            flash('设备名称和设备编码为必填项', 'danger')
            return render_template('device/add.html', device_types=device_types)
        
        # 检查设备编码是否重复
        if Device.query.filter_by(device_code=device_code).first():
            flash('设备编码已存在', 'danger')
            return render_template('device/add.html', device_types=device_types)
        
        # 创建新设备
        new_device = Device(
            name=name,
            device_code=device_code,
            type_id=type_id if type_id else None,
            location=location,
            ip_address=ip_address,
            mac_address=mac_address,
            username=username,
            password=password,
            status=status if status else '正常',
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            purchase_date=purchase_date,
            warranty_period=warranty_period if warranty_period else None,
            notes=notes
        )
        
        try:
            db.session.add(new_device)
            db.session.commit()
            flash('设备添加成功', 'success')
            return redirect(url_for('device.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'设备添加失败: {str(e)}', 'danger')
    
    return render_template('device/add.html', device_types=device_types)

# 编辑设备
@device_bp.route('/edit/<int:device_id>', methods=['GET', 'POST'])
@login_required
def edit(device_id):
    # 获取设备
    device = Device.query.get_or_404(device_id)
    
    # 获取所有设备类型
    device_types = DeviceType.query.all()
    
    if request.method == 'POST':
        # 记录原始位置，用于调试
        original_location = device.location
        
        # 验证必填字段
        name = request.form.get('name')
        device_code = request.form.get('device_code')
        
        if not name or not device_code:
            flash('设备名称和设备编码为必填项', 'danger')
            return render_template('device/edit.html', device=device, device_types=device_types)
        
        # 检查设备编码是否重复（排除自身）
        duplicate = Device.query.filter(
            Device.device_code == device_code,
            Device.id != device_id
        ).first()
        
        if duplicate:
            flash('设备编码已存在', 'danger')
            return render_template('device/edit.html', device=device, device_types=device_types)
            
        # 收集所有要更新的字段
        update_data = {
            'name': name,
            'device_code': device_code,
            'type_id': request.form.get('type_id') or None,
            'location': request.form.get('location'),
            'ip_address': request.form.get('ip_address'),
            'mac_address': request.form.get('mac_address'),
            'username': request.form.get('username'),
            'manufacturer': request.form.get('manufacturer'),
            'model': request.form.get('model'),
            'serial_number': request.form.get('serial_number'),
            'warranty_period': request.form.get('warranty_period'),
            'notes': request.form.get('notes'),
            'status': request.form.get('status')
        }
        
        # 处理密码（只在有输入时更新）
        if request.form.get('password'):
            update_data['password'] = request.form.get('password')
        
        # 处理日期
        if request.form.get('purchase_date'):
            try:
                purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date()
                update_data['purchase_date'] = purchase_date
            except ValueError:
                flash('购买日期格式不正确', 'danger')
                return render_template('device/edit.html', device=device, device_types=device_types)
        
        try:
            # 打印调试信息
            print(f"更新设备位置: 原位置={original_location}, 新位置={update_data['location']}")
            
            # 使用SQL更新语句直接更新设备记录
            query = db.session.query(Device).filter(Device.id == device_id)
            query.update(update_data)
            db.session.commit()
            
            flash('设备更新成功', 'success')
            return redirect(url_for('device.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'设备更新失败: {str(e)}', 'danger')
    
    return render_template('device/edit.html', device=device, device_types=device_types)

# 查看设备详情
@device_bp.route('/view/<int:device_id>')
@login_required
def view(device_id):
    # 使用joinedload预加载设备类型
    device = Device.query.options(joinedload(Device.type)).get_or_404(device_id)
    return render_template('device/view.html', device=device)

# 删除设备
# @device_bp.route('/delete/<int:device_id>', methods=['POST'])
# @login_required
# def delete(device_id):
#     device = Device.query.get_or_404(device_id)
    
#     try:
#         db.session.delete(device)
#         db.session.commit()
#         flash('设备已删除', 'success')
#     except Exception as e:
#         db.session.rollback()
#         flash(f'删除设备失败: {str(e)}', 'danger')
    
#     return redirect(url_for('device.index'))
@device_bp.route('/delete/<int:device_id>', methods=['POST'])
@login_required
def delete(device_id):
    try:
        # 直接使用SQL语句删除设备及相关记录
        # 首先删除外键引用
        db.session.execute(f"DELETE FROM performance_data WHERE device_id = {device_id}")
        db.session.execute(f"DELETE FROM performance_records WHERE device_id = {device_id}")
        db.session.execute(f"DELETE FROM thresholds WHERE device_id = {device_id}")
        # 最后删除设备记录
        db.session.execute(f"DELETE FROM devices WHERE id = {device_id}")
        db.session.commit()
        
        flash('设备已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除设备失败: {str(e)}', 'danger')
    
    return redirect(url_for('device.index'))

# 设备类型管理
@device_bp.route('/types')
@login_required
def types():
    device_types = DeviceType.query.all()
    return render_template('device/types.html', device_types=device_types)

# 添加设备类型
@device_bp.route('/types/add', methods=['GET', 'POST'])
@login_required
def add_type():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('类型名称为必填项', 'danger')
            return render_template('device/add_type.html')
        
        # 检查类型名称是否重复
        if DeviceType.query.filter_by(name=name).first():
            flash('类型名称已存在', 'danger')
            return render_template('device/add_type.html')
        
        new_type = DeviceType(name=name, description=description)
        
        try:
            db.session.add(new_type)
            db.session.commit()
            flash('设备类型添加成功', 'success')
            return redirect(url_for('device.types'))
        except Exception as e:
            db.session.rollback()
            flash(f'设备类型添加失败: {str(e)}', 'danger')
    
    return render_template('device/add_type.html')

# 编辑设备类型
@device_bp.route('/types/edit/<int:type_id>', methods=['GET', 'POST'])
@login_required
def edit_type(type_id):
    device_type = DeviceType.query.get_or_404(type_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('类型名称为必填项', 'danger')
            return render_template('device/edit_type.html', device_type=device_type)
        
        # 检查类型名称是否重复（排除自身）
        duplicate = DeviceType.query.filter(
            DeviceType.name == name,
            DeviceType.id != type_id
        ).first()
        
        if duplicate:
            flash('类型名称已存在', 'danger')
            return render_template('device/edit_type.html', device_type=device_type)
        
        device_type.name = name
        device_type.description = description
        
        try:
            db.session.commit()
            flash('设备类型更新成功', 'success')
            return redirect(url_for('device.types'))
        except Exception as e:
            db.session.rollback()
            flash(f'设备类型更新失败: {str(e)}', 'danger')
    
    return render_template('device/edit_type.html', device_type=device_type)

# 删除设备类型
@device_bp.route('/types/delete/<int:type_id>', methods=['POST'])
@login_required
def delete_type(type_id):
    device_type = DeviceType.query.get_or_404(type_id)
    
    # 检查是否有设备使用此类型
    if device_type.devices.count() > 0:
        flash('无法删除: 有设备正在使用此类型', 'danger')
        return redirect(url_for('device.types'))
    
    try:
        db.session.delete(device_type)
        db.session.commit()
        flash('设备类型已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除设备类型失败: {str(e)}', 'danger')
    
    return redirect(url_for('device.types'))

@device_bp.route('/list')
def device_list():
    """设备列表页面"""
    return render_template('device/list.html')

@device_bp.route('/api/list')
def api_device_list():
    """获取设备列表API"""
    try:
        devices = get_all_devices()
        return jsonify({
            'status': 'success',
            'devices': [device.to_dict() for device in devices]
        })
    except Exception as e:
        logger.error(f"获取设备列表时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取设备列表失败: {str(e)}'
        }), 500

@device_bp.route('/api/info/<int:device_id>')
def api_device_info(device_id):
    """获取设备详细信息API"""
    try:
        result = get_device_info(device_id)
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', '未知错误')
            }), 404
    except Exception as e:
        logger.error(f"获取设备 {device_id} 信息时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取设备信息失败: {str(e)}'
        }), 500

@device_bp.route('/api/test-connection/<int:device_id>')
def api_test_connection(device_id):
    """测试设备连接API"""
    try:
        result = test_device_connection(device_id)
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', '未知错误')
            }), 400
    except Exception as e:
        logger.error(f"测试设备 {device_id} 连接时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'测试连接失败: {str(e)}'
        }), 500

# 添加新的全局API路由，供维护模块使用
@device_bp.route('/api/devices')
def api_devices():
    """设备列表API - 用于维护模块选择设备"""
    try:
        devices = Device.query.order_by(Device.name).all()
        return jsonify([
            {
                'id': device.id,
                'name': device.name,
                'device_code': device.device_code,
                'type': device.type.name if device.type else '未分类',
                'status': device.status
            } for device in devices
        ])
    except Exception as e:
        return jsonify([]), 500