#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
IPSec与防火墙联动策略管理数据库迁移脚本
创建策略相关表
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# 定义JSON类型，兼容不同数据库
JSON = sqlite.JSON

# 修订版本标识
revision = '001_policy_tables'
down_revision = None  # 根据实际情况调整
depends_on = None

def upgrade():
    """升级数据库"""
    # 创建策略表
    op.create_table(
        'policy',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('config', JSON, nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # 创建策略模板表
    op.create_table(
        'policy_template',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('config', JSON, nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    
    # 创建策略部署表
    op.create_table(
        'policy_deployment',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policy.id'), nullable=False),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('device.id'), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('deployed_at', sa.DateTime(), nullable=False),
        sa.Column('deployed_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('config_snapshot', JSON),
        sa.Column('result', sa.Text())
    )
    
    # 创建策略审计日志表
    op.create_table(
        'policy_audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policy.id')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('details', sa.Text()),
        sa.Column('ip_address', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    
    # 创建策略告警表
    op.create_table(
        'policy_alert',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('policy_id', sa.Integer(), sa.ForeignKey('policy.id')),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('device.id')),
        sa.Column('alert_type', sa.String(32), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False, server_default='warning'),
        sa.Column('details', sa.Text()),
        sa.Column('status', sa.String(16), nullable=False, server_default='new'),
        sa.Column('acknowledged_by', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('acknowledged_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    
    # 创建索引
    op.create_index('ix_policy_name', 'policy', ['name'])
    op.create_index('ix_policy_type', 'policy', ['type'])
    op.create_index('ix_policy_status', 'policy', ['status'])
    op.create_index('ix_policy_template_name', 'policy_template', ['name'])
    op.create_index('ix_policy_template_type', 'policy_template', ['type'])
    op.create_index('ix_policy_deployment_status', 'policy_deployment', ['status'])
    op.create_index('ix_policy_audit_log_action', 'policy_audit_log', ['action'])
    op.create_index('ix_policy_alert_status', 'policy_alert', ['status'])
    op.create_index('ix_policy_alert_severity', 'policy_alert', ['severity'])

def downgrade():
    """降级数据库"""
    # 按创建的相反顺序删除表
    op.drop_table('policy_alert')
    op.drop_table('policy_audit_log')
    op.drop_table('policy_deployment')
    op.drop_table('policy_template')
    op.drop_table('policy') 