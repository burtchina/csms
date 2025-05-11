"""创建策略管理相关表

Revision ID: 9f73b4e2a5c2
Revises: previous_revision_id
Create Date: 2023-09-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f73b4e2a5c2'
down_revision = 'previous_revision_id'  # 替换为实际的前一个版本ID
branch_labels = None
depends_on = None


def upgrade():
    # ### 创建策略表 ###
    op.create_table(
        'policy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### 创建策略模板表 ###
    op.create_table(
        'policy_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### 创建策略部署表 ###
    op.create_table(
        'policy_deployment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('deployed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deployed_by', sa.Integer(), nullable=False),
        sa.Column('config_snapshot', sa.JSON(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['deployed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['policy.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### 创建策略审计日志表 ###
    op.create_table(
        'policy_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['policy_id'], ['policy.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### 创建策略告警表 ###
    op.create_table(
        'policy_alert',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=True),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False, server_default='warning'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='new'),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['policy_id'], ['policy.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ### 创建索引 ###
    op.create_index(op.f('ix_policy_name'), 'policy', ['name'], unique=False)
    op.create_index(op.f('ix_policy_type'), 'policy', ['type'], unique=False)
    op.create_index(op.f('ix_policy_status'), 'policy', ['status'], unique=False)
    
    op.create_index(op.f('ix_policy_template_name'), 'policy_template', ['name'], unique=False)
    op.create_index(op.f('ix_policy_template_type'), 'policy_template', ['type'], unique=False)
    
    op.create_index(op.f('ix_policy_deployment_policy_id'), 'policy_deployment', ['policy_id'], unique=False)
    op.create_index(op.f('ix_policy_deployment_device_id'), 'policy_deployment', ['device_id'], unique=False)
    op.create_index(op.f('ix_policy_deployment_status'), 'policy_deployment', ['status'], unique=False)
    
    op.create_index(op.f('ix_policy_audit_log_policy_id'), 'policy_audit_log', ['policy_id'], unique=False)
    op.create_index(op.f('ix_policy_audit_log_user_id'), 'policy_audit_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_policy_audit_log_action'), 'policy_audit_log', ['action'], unique=False)
    
    op.create_index(op.f('ix_policy_alert_policy_id'), 'policy_alert', ['policy_id'], unique=False)
    op.create_index(op.f('ix_policy_alert_device_id'), 'policy_alert', ['device_id'], unique=False)
    op.create_index(op.f('ix_policy_alert_status'), 'policy_alert', ['status'], unique=False)
    op.create_index(op.f('ix_policy_alert_alert_type'), 'policy_alert', ['alert_type'], unique=False)


def downgrade():
    # ### 删除表 ###
    op.drop_table('policy_alert')
    op.drop_table('policy_audit_log')
    op.drop_table('policy_deployment')
    op.drop_table('policy_template')
    op.drop_table('policy') 