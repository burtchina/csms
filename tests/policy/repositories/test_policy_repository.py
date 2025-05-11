#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略管理模块仓库单元测试
"""

import unittest
from datetime import datetime
from src.core.db import db
from src.modules.policy.models.policy import Policy, PolicyTemplate, PolicyDeployment, PolicyAuditLog, PolicyAlert
from src.modules.policy.repositories.policy_repository import (
    PolicyRepository, 
    PolicyTemplateRepository,
    PolicyDeploymentRepository,
    PolicyAuditLogRepository,
    PolicyAlertRepository
)
from tests.base import BaseTestCase

class PolicyRepositoryTestCase(BaseTestCase):
    """策略仓库测试用例"""
    
    def setUp(self):
        super().setUp()
        # 创建测试用户
        self.create_test_user()
        # 创建测试设备
        self.create_test_device()
    
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
    
    def create_test_device(self):
        """创建测试设备"""
        from src.modules.device.models import Device
        if not Device.query.filter_by(name='测试防火墙').first():
            device = Device(
                name='测试防火墙',
                ip_address='192.168.1.1',
                device_type='firewall',
                status='online'
            )
            db.session.add(device)
            db.session.commit()
        self.test_device = Device.query.filter_by(name='测试防火墙').first()
    
    def test_policy_repository_crud(self):
        """测试策略仓库的CRUD操作"""
        # 创建策略
        policy_data = {
            'name': '测试策略仓库',
            'type': 'ipsec',
            'description': '测试策略仓库CRUD',
            'config': {"version": "1.0"},
            'status': 'draft',
            'created_by': self.test_user.id
        }
        
        # 测试创建
        policy = PolicyRepository.create_policy(policy_data)
        self.assertIsNotNone(policy)
        self.assertEqual(policy.name, '测试策略仓库')
        
        # 测试查询
        saved_policy = PolicyRepository.get_policy(policy.id)
        self.assertIsNotNone(saved_policy)
        self.assertEqual(saved_policy.name, '测试策略仓库')
        
        # 测试更新
        update_data = {'name': '更新的策略名称', 'status': 'active'}
        updated_policy = PolicyRepository.update_policy(policy.id, update_data)
        self.assertEqual(updated_policy.name, '更新的策略名称')
        self.assertEqual(updated_policy.status, 'active')
        
        # 测试列表查询
        policies = PolicyRepository.list_policies()
        self.assertTrue(len(policies) > 0)
        self.assertIn(updated_policy, policies)
        
        # 测试筛选查询
        filtered_policies = PolicyRepository.list_policies({'status': 'active'})
        self.assertIn(updated_policy, filtered_policies)
        
        # 测试删除
        result = PolicyRepository.delete_policy(policy.id)
        self.assertTrue(result)
        
        # 验证删除状态
        deleted_policy = PolicyRepository.get_policy(policy.id)
        self.assertEqual(deleted_policy.status, 'deleted')
        
        # 清理
        db.session.delete(deleted_policy)
        db.session.commit()
    
    def test_policy_template_repository(self):
        """测试策略模板仓库"""
        # 创建模板
        template_data = {
            'name': '测试模板仓库',
            'type': 'ipsec',
            'description': '测试模板仓库',
            'config': {"version": "1.0"},
            'is_system': False,
            'created_by': self.test_user.id
        }
        
        # 测试创建
        template = PolicyTemplateRepository.create_template(template_data)
        self.assertIsNotNone(template)
        self.assertEqual(template.name, '测试模板仓库')
        
        # 测试查询
        saved_template = PolicyTemplateRepository.get_template(template.id)
        self.assertIsNotNone(saved_template)
        self.assertEqual(saved_template.name, '测试模板仓库')
        
        # 测试更新
        update_data = {'name': '更新的模板名称'}
        updated_template = PolicyTemplateRepository.update_template(template.id, update_data)
        self.assertEqual(updated_template.name, '更新的模板名称')
        
        # 测试列表查询
        templates = PolicyTemplateRepository.list_templates()
        self.assertTrue(len(templates) > 0)
        self.assertIn(updated_template, templates)
        
        # 测试系统模板保护
        template.is_system = True
        db.session.commit()
        
        # 尝试更新系统模板
        update_result = PolicyTemplateRepository.update_template(template.id, {'name': '不应该更新'})
        self.assertIsNone(update_result)
        
        # 尝试删除系统模板
        delete_result = PolicyTemplateRepository.delete_template(template.id)
        self.assertFalse(delete_result)
        
        # 重置为非系统模板并删除
        template.is_system = False
        db.session.commit()
        
        # 测试删除
        result = PolicyTemplateRepository.delete_template(template.id)
        self.assertTrue(result)
        
        # 验证是否删除
        self.assertIsNone(PolicyTemplateRepository.get_template(template.id))
    
    def test_policy_deployment_repository(self):
        """测试策略部署仓库"""
        # 创建测试策略
        policy = Policy(
            name='测试部署策略',
            type='ipsec',
            description='测试部署策略',
            config={"version": "1.0"},
            status='active',
            created_by=self.test_user.id
        )
        db.session.add(policy)
        db.session.commit()
        
        # 创建部署记录
        deployment_data = {
            'policy_id': policy.id,
            'device_id': self.test_device.id,
            'status': 'pending',
            'deployed_by': self.test_user.id,
            'config_snapshot': {"version": "1.0"},
            'result': ''
        }
        
        # 测试创建
        deployment = PolicyDeploymentRepository.create_deployment(deployment_data)
        self.assertIsNotNone(deployment)
        self.assertEqual(deployment.status, 'pending')
        
        # 测试查询
        saved_deployment = PolicyDeploymentRepository.get_deployment(deployment.id)
        self.assertIsNotNone(saved_deployment)
        self.assertEqual(saved_deployment.policy_id, policy.id)
        
        # 测试更新
        update_data = {'status': 'success', 'result': '部署成功'}
        updated_deployment = PolicyDeploymentRepository.update_deployment(deployment.id, update_data)
        self.assertEqual(updated_deployment.status, 'success')
        self.assertEqual(updated_deployment.result, '部署成功')
        
        # 测试列表查询
        deployments = PolicyDeploymentRepository.list_deployments({'policy_id': policy.id})
        self.assertEqual(len(deployments), 1)
        self.assertEqual(deployments[0].id, deployment.id)
        
        # 测试获取最新部署
        latest_deployment = PolicyDeploymentRepository.get_latest_deployment(policy.id, self.test_device.id)
        self.assertEqual(latest_deployment.id, deployment.id)
        
        # 清理
        db.session.delete(deployment)
        db.session.delete(policy)
        db.session.commit()
    
    def test_policy_audit_log_repository(self):
        """测试策略审计日志仓库"""
        # 创建测试策略
        policy = Policy(
            name='测试审计日志策略',
            type='ipsec',
            description='测试审计日志策略',
            config={"version": "1.0"},
            status='active',
            created_by=self.test_user.id
        )
        db.session.add(policy)
        db.session.commit()
        
        # 创建审计日志
        log_data = {
            'policy_id': policy.id,
            'user_id': self.test_user.id,
            'action': 'create',
            'details': '创建策略',
            'ip_address': '127.0.0.1'
        }
        
        # 测试创建
        log = PolicyAuditLogRepository.create_log(log_data)
        self.assertIsNotNone(log)
        self.assertEqual(log.action, 'create')
        
        # 测试查询
        saved_log = PolicyAuditLogRepository.get_log(log.id)
        self.assertIsNotNone(saved_log)
        self.assertEqual(saved_log.policy_id, policy.id)
        
        # 测试列表查询（带分页）
        logs, total = PolicyAuditLogRepository.list_logs({'policy_id': policy.id}, page=1, per_page=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(total, 1)
        self.assertEqual(logs[0].id, log.id)
        
        # 清理
        db.session.delete(log)
        db.session.delete(policy)
        db.session.commit()
    
    def test_policy_alert_repository(self):
        """测试策略告警仓库"""
        # 创建测试策略
        policy = Policy(
            name='测试告警策略',
            type='ipsec',
            description='测试告警策略',
            config={"version": "1.0"},
            status='active',
            created_by=self.test_user.id
        )
        db.session.add(policy)
        db.session.commit()
        
        # 创建告警
        alert_data = {
            'policy_id': policy.id,
            'device_id': self.test_device.id,
            'alert_type': 'policy_violation',
            'severity': 'warning',
            'details': '策略违规',
            'status': 'new'
        }
        
        # 测试创建
        alert = PolicyAlertRepository.create_alert(alert_data)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, 'policy_violation')
        
        # 测试查询
        saved_alert = PolicyAlertRepository.get_alert(alert.id)
        self.assertIsNotNone(saved_alert)
        self.assertEqual(saved_alert.policy_id, policy.id)
        
        # 测试更新
        update_data = {'severity': 'critical'}
        updated_alert = PolicyAlertRepository.update_alert(alert.id, update_data)
        self.assertEqual(updated_alert.severity, 'critical')
        
        # 测试确认告警
        result = PolicyAlertRepository.acknowledge_alert(alert.id, self.test_user.id)
        self.assertTrue(result)
        
        # 验证确认状态
        acknowledged_alert = PolicyAlertRepository.get_alert(alert.id)
        self.assertEqual(acknowledged_alert.status, 'acknowledged')
        self.assertEqual(acknowledged_alert.acknowledged_by, self.test_user.id)
        
        # 测试解决告警
        result = PolicyAlertRepository.resolve_alert(alert.id)
        self.assertTrue(result)
        
        # 验证解决状态
        resolved_alert = PolicyAlertRepository.get_alert(alert.id)
        self.assertEqual(resolved_alert.status, 'resolved')
        
        # 测试列表查询（带分页）
        alerts, total = PolicyAlertRepository.list_alerts({'policy_id': policy.id}, page=1, per_page=10)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(total, 1)
        self.assertEqual(alerts[0].id, alert.id)
        
        # 清理
        db.session.delete(alert)
        db.session.delete(policy)
        db.session.commit()

if __name__ == '__main__':
    unittest.main() 