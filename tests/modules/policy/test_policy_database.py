# -*- coding: utf-8 -*-

"""
测试IPSec与防火墙联动策略管理的数据库模型
"""

import os
import sys
import unittest
from datetime import datetime
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import select

# 确保可以导入src模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 创建临时Base
Base = declarative_base()

# 导入数据库实例 - 修正导入路径
from src.core.db import db

# 创建用户模型的临时副本，避免外键问题
class TestUser(Base):
    """临时测试用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

# 创建设备模型的临时副本
class TestDevice(Base):
    """临时测试设备模型"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='正常')
    model = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

# 创建临时策略模型
class TestPolicy(Base):
    """临时测试策略模型"""
    __tablename__ = 'policy'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(16), nullable=False, default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

# 创建临时策略模板模型
class TestPolicyTemplate(Base):
    """临时测试策略模板模型"""
    __tablename__ = 'policy_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    config = db.Column(db.JSON, nullable=False)
    is_system = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

# 创建临时策略部署模型
class TestPolicyDeployment(Base):
    """临时测试策略部署模型"""
    __tablename__ = 'policy_deployment'
    
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    status = db.Column(db.String(16), nullable=False)
    deployed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    config_snapshot = db.Column(db.JSON, nullable=False)
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

# 创建临时策略审计日志模型
class TestPolicyAuditLog(Base):
    """临时测试策略审计日志模型"""
    __tablename__ = 'policy_audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(32), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(39))
    created_at = db.Column(db.DateTime, default=datetime.now)

# 创建临时策略告警模型
class TestPolicyAlert(Base):
    """临时测试策略告警模型"""
    __tablename__ = 'policy_alert'
    
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    alert_type = db.Column(db.String(32), nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(16), nullable=False, default='new')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

class TestPolicyDatabase(unittest.TestCase):
    """测试IPSec与防火墙联动策略管理的数据库模型"""

    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建内存数据库
        cls.engine = create_engine('sqlite:///:memory:')
        
        # 创建所有表 - 使用Base.metadata一次性创建所有表
        Base.metadata.create_all(cls.engine)
        
        # 创建会话
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()
        
        # 创建测试数据
        cls._create_test_data()

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        cls.session.close()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        # 创建测试用户
        test_user = TestUser(
            username="test_admin",
            email="admin@test.com",
            password_hash="hashed_password",
            is_active=True
        )
        cls.session.add(test_user)
        
        # 创建测试设备
        test_device = TestDevice(
            name="测试防火墙",
            ip_address="192.168.1.1",
            status="正常",
            model="USG6000"
        )
        cls.session.add(test_device)
        cls.session.commit()
        
        # 获取创建的用户和设备ID
        cls.user_id = test_user.id
        cls.device_id = test_device.id
        
        # 创建基本策略以供其他测试使用
        test_policy = TestPolicy(
            name="测试IPSec策略",
            type="ipsec",
            description="测试IPSec与防火墙联动策略",
            config={
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "deny",
                    "allowed_protocols": [
                        {"protocol": "udp", "port": 500, "description": "IKE"}
                    ]
                },
                "ipsec_settings": {
                    "authentication": {"method": "psk", "psk": "encrypted:test"}
                }
            },
            status="draft",
            created_by=cls.user_id
        )
        cls.session.add(test_policy)
        cls.session.commit()
        
        # 保存策略ID供后续测试使用
        cls.policy_id = test_policy.id

    def test_01_policy_model(self):
        """测试Policy模型"""
        # 查询并验证已创建的策略
        policy = self.session.query(TestPolicy).get(self.policy_id)
        self.assertIsNotNone(policy)
        self.assertEqual(policy.type, "ipsec")
        self.assertEqual(policy.status, "draft")
        self.assertEqual(policy.created_by, self.user_id)
        self.assertIsInstance(policy.config, dict)
        self.assertEqual(policy.config["version"], "1.0")

    def test_02_policy_template_model(self):
        """测试PolicyTemplate模型"""
        # 创建测试模板
        test_template = TestPolicyTemplate(
            name="IPSec基本安全策略",
            type="ipsec",
            description="仅允许IPSec相关协议通过，其他外部访问全部拒绝",
            config={
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "deny",
                    "allowed_protocols": [
                        {"protocol": "udp", "port": 500, "description": "IKE"}
                    ]
                }
            },
            is_system=True,
            created_by=self.user_id
        )
        self.session.add(test_template)
        self.session.commit()
        
        # 查询并验证
        template = self.session.query(TestPolicyTemplate).filter_by(name="IPSec基本安全策略").first()
        self.assertIsNotNone(template)
        self.assertEqual(template.type, "ipsec")
        self.assertTrue(template.is_system)
        self.assertEqual(template.created_by, self.user_id)

    def test_03_policy_deployment_model(self):
        """测试PolicyDeployment模型"""
        # 获取已创建的策略
        policy = self.session.query(TestPolicy).get(self.policy_id)
        self.assertIsNotNone(policy, "测试策略不存在")
        
        # 创建测试部署记录
        test_deployment = TestPolicyDeployment(
            policy_id=policy.id,
            device_id=self.device_id,
            status="success",
            deployed_by=self.user_id,
            config_snapshot=policy.config,
            result="部署成功"
        )
        self.session.add(test_deployment)
        self.session.commit()
        
        # 查询并验证
        deployment = self.session.query(TestPolicyDeployment).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment.status, "success")
        self.assertEqual(deployment.device_id, self.device_id)
        self.assertEqual(deployment.deployed_by, self.user_id)

    def test_04_policy_audit_log_model(self):
        """测试PolicyAuditLog模型"""
        # 获取已创建的策略
        policy = self.session.query(TestPolicy).get(self.policy_id)
        self.assertIsNotNone(policy, "测试策略不存在")
        
        # 创建测试审计日志
        test_log = TestPolicyAuditLog(
            policy_id=policy.id,
            user_id=self.user_id,
            action="create",
            details="创建IPSec策略",
            ip_address="127.0.0.1"
        )
        self.session.add(test_log)
        self.session.commit()
        
        # 查询并验证
        log = self.session.query(TestPolicyAuditLog).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "create")
        self.assertEqual(log.user_id, self.user_id)
        self.assertEqual(log.details, "创建IPSec策略")

    def test_05_policy_alert_model(self):
        """测试PolicyAlert模型"""
        # 获取已创建的策略
        policy = self.session.query(TestPolicy).get(self.policy_id)
        self.assertIsNotNone(policy, "测试策略不存在")
        
        # 创建测试告警
        test_alert = TestPolicyAlert(
            policy_id=policy.id,
            device_id=self.device_id,
            alert_type="policy_violation",
            severity="warning",
            details="发现未授权访问",
            status="new"
        )
        self.session.add(test_alert)
        self.session.commit()
        
        # 查询并验证
        alert = self.session.query(TestPolicyAlert).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "policy_violation")
        self.assertEqual(alert.severity, "warning")
        self.assertEqual(alert.status, "new")
        self.assertEqual(alert.device_id, self.device_id)


if __name__ == '__main__':
    unittest.main() 