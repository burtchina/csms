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
    return redirect(url_for('index'))

# 注册路由
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from src.modules.auth.models import User
    from src.app import db
    
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