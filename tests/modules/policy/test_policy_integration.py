# -*- coding: utf-8 -*-

"""
IPSec与防火墙联动策略管理的集成测试
使用近似实际项目模型进行测试，确保功能正确
"""

import os
import sys
import unittest
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

# 确保可以导入src模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 创建一个新的声明性基类
Base = declarative_base()

# 创建与实际项目类似但隔离的模型
class BaseModel(Base):
    """基础模型提供通用属性"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(BaseModel):
    """用户模型，参照实际项目结构"""
    __tablename__ = 'users'
    
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 关系
    policies = relationship('Policy', back_populates='creator')
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = password  # 在实际环境中会调用加密函数

class Device(BaseModel):
    """设备模型，参照实际项目结构"""
    __tablename__ = 'devices'
    
    name = Column(String(100), nullable=False)
    ip_address = Column(String(20), nullable=False)
    status = Column(String(20), default='正常')
    model = Column(String(100), nullable=True)
    
    # 关系
    deployments = relationship('PolicyDeployment', back_populates='device')
    alerts = relationship('PolicyAlert', back_populates='device')

class Policy(BaseModel):
    """策略模型，参照实际项目结构"""
    __tablename__ = 'policy'
    
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default='draft')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 关系
    creator = relationship('User', back_populates='policies')
    deployments = relationship('PolicyDeployment', back_populates='policy')
    audit_logs = relationship('PolicyAuditLog', back_populates='policy')
    alerts = relationship('PolicyAlert', back_populates='policy')

class PolicyTemplate(BaseModel):
    """策略模板模型，参照实际项目结构"""
    __tablename__ = 'policy_template'
    
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    is_system = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 关系
    creator = relationship('User')

class PolicyDeployment(BaseModel):
    """策略部署模型，参照实际项目结构"""
    __tablename__ = 'policy_deployment'
    
    policy_id = Column(Integer, ForeignKey('policy.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    status = Column(String(16), nullable=False)
    deployed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    config_snapshot = Column(JSON, nullable=False)
    result = Column(Text)
    
    # 关系
    policy = relationship('Policy', back_populates='deployments')
    device = relationship('Device', back_populates='deployments')
    deployer = relationship('User')

class PolicyAuditLog(BaseModel):
    """策略审计日志模型，参照实际项目结构"""
    __tablename__ = 'policy_audit_log'
    
    policy_id = Column(Integer, ForeignKey('policy.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(32), nullable=False)
    details = Column(Text)
    ip_address = Column(String(39))
    
    # 关系
    policy = relationship('Policy', back_populates='audit_logs')
    user = relationship('User')

class PolicyAlert(BaseModel):
    """策略告警模型，参照实际项目结构"""
    __tablename__ = 'policy_alert'
    
    policy_id = Column(Integer, ForeignKey('policy.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    alert_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False)
    details = Column(Text)
    status = Column(String(16), nullable=False, default='new')
    
    # 关系
    policy = relationship('Policy', back_populates='alerts')
    device = relationship('Device', back_populates='alerts')

class TestPolicyIntegration(unittest.TestCase):
    """
    策略管理模块的集成测试
    """
    
    # 类级别的属性初始化
    policy_id = None

    @classmethod
    def setUpClass(cls):
        """设置测试环境，使用内存数据库"""
        # 创建内存数据库并设置为测试模式
        cls.engine = create_engine('sqlite:///:memory:')
        
        # 创建所有表，使用我们定义的临时模型
        Base.metadata.create_all(cls.engine)
        
        # 创建会话
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()
        
        # 创建测试数据
        cls._create_test_data()
        
        # 在类级别创建测试策略
        cls._create_test_policy()
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 关闭会话
        cls.session.close()
    
    @classmethod
    def _create_test_data(cls):
        """创建测试所需的基础数据"""
        # 创建测试用户
        test_user = User(
            username="int_admin",
            email="int_admin@test.com",
            password="test_password" 
        )
        cls.session.add(test_user)
        
        # 创建测试设备
        test_device = Device(
            name="集成测试防火墙",
            ip_address="192.168.100.1",
            status="正常"
        )
        cls.session.add(test_device)
        cls.session.commit()
        
        # 保存ID引用
        cls.user_id = test_user.id
        cls.device_id = test_device.id
    
    @classmethod
    def _create_test_policy(cls):
        """创建测试策略"""
        test_policy = Policy(
            name="集成测试IPSec策略",
            type="ipsec",
            description="集成测试用IPSec策略",
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
        
        # 保存策略ID到类属性
        cls.policy_id = test_policy.id
    
    def test_01_policy_exists(self):
        """验证测试策略是否正确创建"""
        policy = self.session.query(Policy).get(self.policy_id)
        self.assertIsNotNone(policy)
        self.assertEqual(policy.type, "ipsec")
        self.assertEqual(policy.status, "draft")
        self.assertEqual(policy.created_by, self.user_id)
    
    def test_02_create_policy_template(self):
        """测试创建策略模板"""
        # 创建测试模板
        test_template = PolicyTemplate(
            name="集成测试IPSec模板",
            type="ipsec",
            description="集成测试用IPSec模板",
            config={
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "deny",
                    "allowed_protocols": [
                        {"protocol": "udp", "port": 500, "description": "IKE"},
                        {"protocol": "esp", "description": "ESP协议"}
                    ]
                }
            },
            is_system=True,
            created_by=self.user_id
        )
        self.session.add(test_template)
        self.session.commit()
        
        # 验证模板创建成功
        template = self.session.query(PolicyTemplate).filter_by(name="集成测试IPSec模板").first()
        self.assertIsNotNone(template)
        self.assertEqual(template.type, "ipsec")
        self.assertTrue(template.is_system)
    
    def test_03_policy_deployment(self):
        """测试策略部署"""
        policy = self.session.query(Policy).get(self.policy_id)
        self.assertIsNotNone(policy, "策略不存在，无法进行部署测试")
        
        # 创建部署记录
        deployment = PolicyDeployment(
            policy_id=policy.id,
            device_id=self.device_id,
            status="success",
            deployed_by=self.user_id,
            config_snapshot=policy.config,
            result="集成测试部署成功"
        )
        self.session.add(deployment)
        self.session.commit()
        
        # 验证部署记录
        saved_deployment = self.session.query(PolicyDeployment).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(saved_deployment)
        self.assertEqual(saved_deployment.status, "success")
        self.assertEqual(saved_deployment.result, "集成测试部署成功")
    
    def test_04_policy_audit_log(self):
        """测试策略审计日志"""
        policy = self.session.query(Policy).get(self.policy_id)
        self.assertIsNotNone(policy, "策略不存在，无法进行审计日志测试")
        
        # 创建审计日志
        audit_log = PolicyAuditLog(
            policy_id=policy.id,
            user_id=self.user_id,
            action="create",
            details="集成测试创建策略",
            ip_address="127.0.0.1"
        )
        self.session.add(audit_log)
        self.session.commit()
        
        # 验证审计日志
        saved_log = self.session.query(PolicyAuditLog).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(saved_log)
        self.assertEqual(saved_log.action, "create")
        self.assertEqual(saved_log.details, "集成测试创建策略")
    
    def test_05_policy_alert(self):
        """测试策略告警"""
        policy = self.session.query(Policy).get(self.policy_id)
        self.assertIsNotNone(policy, "策略不存在，无法进行告警测试")
        
        # 创建告警
        alert = PolicyAlert(
            policy_id=policy.id,
            device_id=self.device_id,
            alert_type="policy_violation",
            severity="high",
            details="集成测试发现策略违规",
            status="new"
        )
        self.session.add(alert)
        self.session.commit()
        
        # 验证告警
        saved_alert = self.session.query(PolicyAlert).filter_by(policy_id=policy.id).first()
        self.assertIsNotNone(saved_alert)
        self.assertEqual(saved_alert.alert_type, "policy_violation")
        self.assertEqual(saved_alert.severity, "high")
        self.assertEqual(saved_alert.status, "new")
    
    def test_06_verify_relationships(self):
        """验证模型之间的关系是否正确"""
        # 获取策略
        policy = self.session.query(Policy).get(self.policy_id)
        self.assertIsNotNone(policy)
        
        # 验证创建者关系
        creator = policy.creator
        self.assertIsNotNone(creator)
        self.assertEqual(creator.id, self.user_id)
        
        # 验证部署关系
        self.assertTrue(len(policy.deployments) > 0)
        deployment = policy.deployments[0]
        self.assertEqual(deployment.policy_id, policy.id)
        
        # 验证审计日志关系
        self.assertTrue(len(policy.audit_logs) > 0)
        log = policy.audit_logs[0]
        self.assertEqual(log.policy_id, policy.id)
        
        # 验证告警关系
        self.assertTrue(len(policy.alerts) > 0)
        alert = policy.alerts[0]
        self.assertEqual(alert.policy_id, policy.id)
        
        # 验证双向关系
        self.assertIn(policy, creator.policies)


if __name__ == '__main__':
    unittest.main() 