#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理模块模型单元测试
"""

import unittest
import json
from datetime import datetime
from src.core.db import db
from src.modules.policy.models.policy import Policy, PolicyTemplate, PolicyDeployment, PolicyAuditLog, PolicyAlert
from tests.base import BaseTestCase

class PolicyModelTestCase(BaseTestCase):
    """策略模型测试用例"""
    
    def setUp(self):
        super().setUp()
        # 创建测试用户
        self.create_test_user()
    
    def create_test_user(self):
        """创建测试用户"""
        from src.modules.auth.models import User
        if not User.query.filter_by(username='testuser').first():
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
        self.test_user = User.query.filter_by(username='testuser').first()
    
    def test_policy_model(self):
        """测试策略模型"""
        # 创建测试策略
        config = {
            "version": "1.0",
            "firewall_settings": {
                "default_action": "deny",
                "allowed_protocols": [
                    {
                        "protocol": "udp",
                        "port": 500,
                        "description": "IKE"
                    }
                ]
            },
            "ipsec_settings": {
                "authentication": {
                    "method": "psk",
                    "psk": "test123"
                },
                "encryption": {
                    "phase1": ["aes-256", "sha256"],
                    "phase2": ["aes-256", "sha256"]
                },
                "lifetime": {
                    "phase1": 86400,
                    "phase2": 3600
                }
            },
            "tunnel_settings": {
                "local_subnet": "192.168.1.0/24",
                "remote_subnet": "192.168.2.0/24",
                "remote_gateway": "203.0.113.1"
            }
        }
        
        policy = Policy(
            name='测试策略',
            type='ipsec',
            description='这是一个测试策略',
            config=config,
            status='draft',
            created_by=self.test_user.id
        )
        
        db.session.add(policy)
        db.session.commit()
        
        # 验证策略是否创建成功
        saved_policy = Policy.query.filter_by(name='测试策略').first()
        self.assertIsNotNone(saved_policy)
        self.assertEqual(saved_policy.type, 'ipsec')
        self.assertEqual(saved_policy.status, 'draft')
        self.assertDictEqual(saved_policy.config, config)
        
        # 测试to_dict方法
        policy_dict = saved_policy.to_dict()
        self.assertEqual(policy_dict['name'], '测试策略')
        self.assertEqual(policy_dict['type'], 'ipsec')
        self.assertEqual(policy_dict['status'], 'draft')
        
        # 测试关系
        self.assertEqual(saved_policy.creator.id, self.test_user.id)
        
        # 清理
        db.session.delete(saved_policy)
        db.session.commit()
    
    def test_policy_template_model(self):
        """测试策略模板模型"""
        # 创建测试模板
        config = {
            "version": "1.0",
            "firewall_settings": {
                "default_action": "deny",
                "allowed_protocols": [
                    {
                        "protocol": "udp",
                        "port": 500,
                        "description": "IKE"
                    }
                ]
            },
            "ipsec_settings": {
                "authentication": {
                    "method": "psk",
                    "psk": ""
                },
                "encryption": {
                    "phase1": ["aes-256", "sha256"],
                    "phase2": ["aes-256", "sha256"]
                },
                "lifetime": {
                    "phase1": 86400,
                    "phase2": 3600
                }
            },
            "tunnel_settings": {
                "local_subnet": "",
                "remote_subnet": "",
                "remote_gateway": ""
            }
        }
        
        template = PolicyTemplate(
            name='IPSec基本模板',
            type='ipsec',
            description='基本IPSec模板',
            config=config,
            is_system=True,
            created_by=self.test_user.id
        )
        
        db.session.add(template)
        db.session.commit()
        
        # 验证模板是否创建成功
        saved_template = PolicyTemplate.query.filter_by(name='IPSec基本模板').first()
        self.assertIsNotNone(saved_template)
        self.assertEqual(saved_template.type, 'ipsec')
        self.assertTrue(saved_template.is_system)
        self.assertDictEqual(saved_template.config, config)
        
        # 测试to_dict方法
        template_dict = saved_template.to_dict()
        self.assertEqual(template_dict['name'], 'IPSec基本模板')
        self.assertEqual(template_dict['type'], 'ipsec')
        self.assertTrue(template_dict['is_system'])
        
        # 测试关系
        self.assertEqual(saved_template.creator.id, self.test_user.id)
        
        # 清理
        db.session.delete(saved_template)
        db.session.commit()
    
    def test_policy_relationships(self):
        """测试策略与其他模型的关系"""
        from src.modules.device.models import Device
        
        # 创建测试设备
        device = Device(
            name='测试防火墙',
            ip_address='192.168.1.1',
            device_type='firewall',
            status='online'
        )
        db.session.add(device)
        db.session.commit()
        
        # 创建测试策略
        policy = Policy(
            name='测试策略关系',
            type='ipsec',
            description='测试策略关系',
            config={"version": "1.0"},
            status='active',
            created_by=self.test_user.id
        )
        db.session.add(policy)
        db.session.commit()
        
        # 创建部署记录
        deployment = PolicyDeployment(
            policy_id=policy.id,
            device_id=device.id,
            status='success',
            deployed_by=self.test_user.id,
            config_snapshot={"version": "1.0"},
            result='部署成功'
        )
        db.session.add(deployment)
        
        # 创建审计日志
        audit_log = PolicyAuditLog(
            policy_id=policy.id,
            user_id=self.test_user.id,
            action='create',
            details='创建策略',
            ip_address='127.0.0.1'
        )
        db.session.add(audit_log)
        
        # 创建告警
        alert = PolicyAlert(
            policy_id=policy.id,
            device_id=device.id,
            alert_type='policy_violation',
            severity='warning',
            details='策略违规',
            status='new'
        )
        db.session.add(alert)
        
        db.session.commit()
        
        # 验证关系
        saved_policy = Policy.query.get(policy.id)
        
        # 测试部署关系
        self.assertEqual(len(saved_policy.deployments), 1)
        self.assertEqual(saved_policy.deployments[0].status, 'success')
        self.assertEqual(saved_policy.deployments[0].device_id, device.id)
        
        # 测试审计日志关系
        self.assertEqual(len(saved_policy.audit_logs), 1)
        self.assertEqual(saved_policy.audit_logs[0].action, 'create')
        
        # 测试告警关系
        self.assertEqual(len(saved_policy.alerts), 1)
        self.assertEqual(saved_policy.alerts[0].alert_type, 'policy_violation')
        
        # 清理
        db.session.delete(alert)
        db.session.delete(audit_log)
        db.session.delete(deployment)
        db.session.delete(policy)
        db.session.delete(device)
        db.session.commit()

if __name__ == '__main__':
    unittest.main() 