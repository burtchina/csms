#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
认证相关路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

# 登录路由
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from src.modules.auth.models import User
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        # 简单演示登录，实际应用中应查询数据库
        # 这里我们创建一个临时用户
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # 更新最后登录时间
            from datetime import datetime
            from src.core.db import db
            user.last_login = datetime.now()
            db.session.commit()
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
            
    return render_template('auth/login.html')

# 注销路由
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('dashboard'))

# 注册路由
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from src.modules.auth.models import User
    from src.core.db import db
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('auth/register.html')
            
        # 创建新用户
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

# 密码重置路由
@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    # TODO: 实现密码重置逻辑
    return render_template('auth/reset_password.html')

# 个人信息路由
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # 获取表单数据
        display_name = request.form.get('display_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # 更新用户信息
        if current_user.email != email:
            from src.modules.auth.models import User
            # 检查邮箱是否已被使用
            if User.query.filter_by(email=email).first() and User.query.filter_by(email=email).first().id != current_user.id:
                flash('该邮箱已被使用', 'danger')
                return redirect(url_for('auth.profile'))
                
        # 更新用户信息
        from src.core.db import db
        current_user.display_name = display_name
        current_user.email = email
        current_user.phone = phone
        db.session.commit()
        
        flash('个人信息已更新', 'success')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html')

# 账号设置路由
@auth_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # 修改密码
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码不正确', 'danger')
            return redirect(url_for('auth.settings'))
            
        # 验证新密码
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('auth.settings'))
            
        # 更新密码
        current_user.set_password(new_password)
        from src.core.db import db
        db.session.commit()
        
        flash('密码已更新', 'success')
        return redirect(url_for('auth.settings'))
        
    return render_template('auth/settings.html') 