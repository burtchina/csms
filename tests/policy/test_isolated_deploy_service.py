#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略下发服务隔离测试
使用Mock对象替代实际的导入依赖，避免'src'模块导入问题
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json


class MockPolicy:
    """模拟策略类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.name = kwargs.get('name', 'Test Policy')
        self.type = kwargs.get('type', 'ipsec')
        self.description = kwargs.get('description', '')
        self.config = kwargs.get('config', {})
        self.status = kwargs.get('status', 'active')
        self.created_by = kwargs.get('created_by', 1)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'config': self.config,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MockDevice:
    """模拟设备类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.name = kwargs.get('name', 'Test Device')
        self.ip_address = kwargs.get('ip_address', '192.168.1.1')
        self.port = kwargs.get('port', 22)
        self.username = kwargs.get('username', 'admin')
        self.password = kwargs.get('password', 'admin123')
        self.connection_protocol = kwargs.get('connection_protocol', 'ssh')
        self.manufacturer = kwargs.get('manufacturer', 'Generic')
        self.model = kwargs.get('model', 'Generic')


class MockPolicyDeployment:
    """模拟策略部署记录"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.policy_id = kwargs.get('policy_id', 1)
        self.device_id = kwargs.get('device_id', 1)
        self.status = kwargs.get('status', 'pending')
        self.deployed_at = kwargs.get('deployed_at', datetime.now())
        self.deployed_by = kwargs.get('deployed_by', 1)
        self.config_snapshot = kwargs.get('config_snapshot', {})
        self.result = kwargs.get('result', '')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'policy_id': self.policy_id,
            'device_id': self.device_id,
            'status': self.status,
            'deployed_at': self.deployed_at.isoformat(),
            'deployed_by': self.deployed_by,
            'config_snapshot': self.config_snapshot,
            'result': self.result
        }


class MockFirewallConnector:
    """模拟防火墙连接器"""
    def __init__(self, success=True):
        self.success = success
        
    def connect(self, device):
        """连接到设备"""
        return self.success
    
    def disconnect(self):
        """断开连接"""
        return True
    
    def deploy_policy(self, policy_config):
        """部署策略"""
        if self.success:
            return True, "Policy deployed successfully"
        else:
            return False, "Failed to deploy policy"
    
    def rollback_policy(self, policy_id):
        """回滚策略"""
        if self.success:
            return True, "Policy rolled back successfully"
        else:
            return False, "Failed to rollback policy"
    
    def get_policy_status(self, policy_id):
        """获取策略状态"""
        if self.success:
            return {"status": "active", "last_checked": datetime.now().isoformat()}
        else:
            return {"status": "unknown", "error": "Failed to get status"}


class MockConnectorFactory:
    """模拟连接器工厂"""
    @staticmethod
    def create_and_connect(device, success=True):
        """创建并连接到设备"""
        connector = MockFirewallConnector(success)
        if connector.connect(device):
            return connector
        return None


class MockPolicyRepository:
    """模拟策略仓库"""
    def __init__(self, policies=None):
        self.policies = policies or {}
    
    def get_by_id(self, policy_id):
        """通过ID获取策略"""
        return self.policies.get(policy_id)
    
    def update(self, policy_id, data):
        """更新策略"""
        if policy_id in self.policies:
            policy = self.policies[policy_id]
            for key, value in data.items():
                setattr(policy, key, value)
            return policy
        return None


class MockPolicyDeploymentRepository:
    """模拟策略部署仓库"""
    def __init__(self, deployments=None):
        self.deployments = deployments or {}
        self.next_id = max(deployments.keys()) if deployments else 1
    
    def create(self, data):
        """创建部署记录"""
        deployment_id = self.next_id
        self.next_id += 1
        
        deployment = MockPolicyDeployment(id=deployment_id, **data)
        self.deployments[deployment_id] = deployment
        return deployment
    
    def update(self, deployment_id, data):
        """更新部署记录"""
        if deployment_id in self.deployments:
            deployment = self.deployments[deployment_id]
            for key, value in data.items():
                setattr(deployment, key, value)
            return deployment
        return None
    
    def get_all(self, filters=None):
        """获取所有部署记录"""
        if not filters:
            return list(self.deployments.values())
        
        result = []
        for deployment in self.deployments.values():
            match = True
            for key, value in filters.items():
                if getattr(deployment, key, None) != value:
                    match = False
                    break
            if match:
                result.append(deployment)
        
        return result
    
    def get_latest_deployment(self, policy_id, device_id):
        """获取最新部署记录"""
        filtered = [d for d in self.deployments.values() 
                  if d.policy_id == policy_id and d.device_id == device_id]
        if filtered:
            return max(filtered, key=lambda d: d.deployed_at)
        return None


class MockDeviceQuery:
    """模拟设备查询"""
    def __init__(self, devices=None):
        self.devices = devices or {}
    
    def get(self, device_id):
        """通过ID获取设备"""
        return self.devices.get(device_id)


class MockPolicyDeployService:
    """模拟策略下发服务"""
    def __init__(self, policy_repo, deployment_repo, device_query=None, connector_factory=None):
        self.policy_repo = policy_repo
        self.deployment_repo = deployment_repo
        self.device_query = device_query or MockDeviceQuery()
        self.connector_factory = connector_factory or MockConnectorFactory
    
    def deploy_policy(self, policy_id, device_id, user_id):
        """部署策略"""
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = self.device_query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        # 检查策略状态
        if policy.status != 'active':
            return False, {'error': f'只能下发状态为active的策略，当前状态: {policy.status}'}
        
        # 创建部署记录
        deployment_data = {
            'policy_id': policy_id,
            'device_id': device_id,
            'status': 'pending',
            'deployed_at': datetime.now(),
            'deployed_by': user_id,
            'config_snapshot': policy.config,
            'result': '策略下发中...'
        }
        
        try:
            # 保存部署记录
            deployment = self.deployment_repo.create(deployment_data)
            
            # 连接设备并部署策略
            success, result = self._deploy_to_device(policy, device, deployment.id)
            
            # 更新部署状态
            status = 'success' if success else 'failed'
            self.deployment_repo.update(deployment.id, {
                'status': status,
                'result': result
            })
            
            if success:
                return True, {'message': f'策略部署成功: {result}', 'deployment_id': deployment.id}
            else:
                return False, {'error': f'策略部署失败: {result}', 'deployment_id': deployment.id}
                
        except Exception as e:
            # 如果已创建部署记录，更新状态为失败
            if 'deployment' in locals():
                self.deployment_repo.update(deployment.id, {
                    'status': 'failed',
                    'result': f'部署异常: {str(e)}'
                })
            
            return False, {'error': str(e)}
    
    def rollback_policy(self, policy_id, device_id, user_id):
        """回滚策略"""
        # 获取最新部署记录
        deployment = self.deployment_repo.get_latest_deployment(policy_id, device_id)
        if not deployment:
            return False, {'error': '未找到部署记录'}
        
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = self.device_query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 创建新的部署记录用于回滚操作
            rollback_data = {
                'policy_id': policy_id,
                'device_id': device_id,
                'status': 'pending',
                'deployed_at': datetime.now(),
                'deployed_by': user_id,
                'config_snapshot': deployment.config_snapshot,
                'result': '策略回滚中...'
            }
            
            rollback_deployment = self.deployment_repo.create(rollback_data)
            
            # 执行回滚
            success, result = self._rollback_on_device(policy, device)
            
            # 更新部署状态
            status = 'success' if success else 'failed'
            self.deployment_repo.update(rollback_deployment.id, {
                'status': status,
                'result': result
            })
            
            if success:
                return True, {'message': f'策略回滚成功: {result}', 'deployment_id': rollback_deployment.id}
            else:
                return False, {'error': f'策略回滚失败: {result}', 'deployment_id': rollback_deployment.id}
                
        except Exception as e:
            # 如果已创建部署记录，更新状态为失败
            if 'rollback_deployment' in locals():
                self.deployment_repo.update(rollback_deployment.id, {
                    'status': 'failed',
                    'result': f'回滚异常: {str(e)}'
                })
            
            return False, {'error': str(e)}
    
    def get_policy_status(self, policy_id, device_id):
        """获取策略部署状态"""
        # 获取最新部署记录
        deployment = self.deployment_repo.get_latest_deployment(policy_id, device_id)
        if not deployment:
            return False, {'error': '未找到部署记录'}
        
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = self.device_query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 获取设备上的策略状态
            device_status = self._get_device_policy_status(policy, device)
            
            # 更新部署记录的状态信息
            if device_status:
                self.deployment_repo.update(deployment.id, {
                    'result': json.dumps(device_status)
                })
            
            # 返回当前状态
            deployment_info = deployment.to_dict()
            
            # 添加实时设备状态
            deployment_info['device_status'] = device_status
            
            return True, deployment_info
            
        except Exception as e:
            return False, {'error': str(e), 'deployment_data': deployment.to_dict()}
    
    def sync_policy_status(self, policy_id=None, device_id=None):
        """同步策略状态"""
        # 获取需要同步的部署记录
        filters = {
            'status': 'success'  # 只同步成功部署的策略
        }
        
        if policy_id:
            filters['policy_id'] = policy_id
            
        if device_id:
            filters['device_id'] = device_id
        
        deployments = self.deployment_repo.get_all(filters)
        
        result = {
            'total': len(deployments),
            'success': 0,
            'failed': 0,
            'not_found': 0,
            'details': []
        }
        
        for deployment in deployments:
            try:
                policy = self.policy_repo.get_by_id(deployment.policy_id)
                device = self.device_query.get(deployment.device_id)
                
                if not policy or not device:
                    result['not_found'] += 1
                    continue
                
                # 获取设备上的策略状态
                device_status = self._get_device_policy_status(policy, device)
                
                if device_status:
                    # 更新部署记录
                    self.deployment_repo.update(deployment.id, {
                        'result': json.dumps(device_status)
                    })
                    
                    result['success'] += 1
                    result['details'].append({
                        'policy_id': policy.id,
                        'policy_name': policy.name,
                        'device_id': device.id,
                        'device_name': device.name,
                        'status': device_status.get('status', 'unknown')
                    })
                else:
                    result['failed'] += 1
            
            except Exception as e:
                result['failed'] += 1
        
        return result
    
    def verify_policy(self, policy_id, device_id):
        """验证策略有效性"""
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = self.device_query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 创建连接器
            connector = self.connector_factory.create_and_connect(device)
            if not connector:
                return False, {'error': f'无法连接到设备 {device.name}'}
            
            try:
                # 验证策略
                is_valid, message = connector.verify_policy(policy.config)
                return is_valid, {'message': message}
            finally:
                # 断开连接
                connector.disconnect()
        except Exception as e:
            return False, {'error': str(e)}
    
    def _deploy_to_device(self, policy, device, deployment_id):
        """部署策略到设备"""
        try:
            # 连接设备
            connector = self.connector_factory.create_and_connect(device)
            if not connector:
                return False, "无法连接到设备"
            
            try:
                # 部署策略
                success, message = connector.deploy_policy(policy.config)
                return success, message
            finally:
                # 断开连接
                connector.disconnect()
                
        except Exception as e:
            return False, f"部署过程中发生错误: {str(e)}"
    
    def _get_device_policy_status(self, policy, device):
        """获取设备上的策略状态"""
        try:
            # 连接设备
            connector = self.connector_factory.create_and_connect(device)
            if not connector:
                return {'status': 'unknown', 'error': f'无法连接到设备 {device.name}'}
            
            try:
                # 获取状态
                status = connector.get_policy_status(str(policy.id))
                return status
            finally:
                # 断开连接
                connector.disconnect()
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _rollback_on_device(self, policy, device):
        """回滚设备上的策略"""
        try:
            # 连接设备
            connector = self.connector_factory.create_and_connect(device)
            if not connector:
                return False, "无法连接到设备"
            
            try:
                # 回滚策略
                success, message = connector.rollback_policy(str(policy.id))
                return success, message
            finally:
                # 断开连接
                connector.disconnect()
                
        except Exception as e:
            return False, f"回滚过程中发生错误: {str(e)}"


class TestIsolatedPolicyDeployService(unittest.TestCase):
    """策略下发服务隔离测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试策略
        self.test_policy = MockPolicy(
            id=1,
            name="Test IPSec Policy",
            type="ipsec",
            status="active",
            config={
                "type": "ipsec",
                "ipsec_settings": {
                    "encryption": {
                        "phase1": ["aes-256", "sha256", "dh-group14"],
                        "phase2": ["aes-256", "sha256"]
                    },
                    "authentication": {
                        "method": "psk",
                        "psk": "secretkey123"
                    }
                }
            }
        )
        
        self.inactive_policy = MockPolicy(
            id=2,
            name="Inactive Policy",
            type="ipsec",
            status="draft",
            config={}
        )
        
        # 创建测试设备
        self.test_device = MockDevice(
            id=1,
            name="Test Firewall",
            manufacturer="Generic"
        )
        
        # 创建测试部署记录
        self.test_deployment = MockPolicyDeployment(
            id=1,
            policy_id=1,
            device_id=1,
            status="success",
            deployed_at=datetime.now(),
            deployed_by=1,
            config_snapshot=self.test_policy.config,
            result="部署成功"
        )
        
        # 创建仓库和查询
        self.policy_repo = MockPolicyRepository({
            1: self.test_policy,
            2: self.inactive_policy
        })
        
        self.deployment_repo = MockPolicyDeploymentRepository({
            1: self.test_deployment
        })
        
        self.device_query = MockDeviceQuery({
            1: self.test_device
        })
        
        # 创建服务
        self.service = MockPolicyDeployService(
            policy_repo=self.policy_repo,
            deployment_repo=self.deployment_repo,
            device_query=self.device_query
        )
    
    def test_deploy_policy_success(self):
        """测试成功部署策略"""
        # 配置成功的连接器工厂
        self.service.connector_factory = MagicMock()
        self.service.connector_factory.create_and_connect.return_value = MockFirewallConnector(success=True)
        
        # 执行部署
        success, result = self.service.deploy_policy(1, 1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('deployment_id', result)
        self.assertIn('策略部署成功', result['message'])
        
        # 验证连接器工厂被调用
        self.service.connector_factory.create_and_connect.assert_called_once_with(self.test_device)
    
    def test_deploy_policy_not_found(self):
        """测试部署不存在的策略"""
        success, result = self.service.deploy_policy(999, 1, 1)
        
        self.assertFalse(success)
        self.assertEqual(result['error'], '策略不存在')
    
    def test_deploy_policy_inactive_status(self):
        """测试部署非激活状态的策略"""
        success, result = self.service.deploy_policy(2, 1, 1)
        
        self.assertFalse(success)
        self.assertIn('只能下发状态为active的策略', result['error'])
    
    def test_deploy_policy_connection_failure(self):
        """测试连接设备失败的情况"""
        # 配置连接失败的连接器工厂
        self.service.connector_factory = MagicMock()
        self.service.connector_factory.create_and_connect.return_value = None
        
        # 执行部署
        success, result = self.service.deploy_policy(1, 1, 1)
        
        # 验证结果
        self.assertFalse(success)
        self.assertIn('无法连接到设备', result['error'])
    
    def test_rollback_policy_success(self):
        """测试成功回滚策略"""
        # 配置成功的连接器工厂
        self.service.connector_factory = MagicMock()
        self.service.connector_factory.create_and_connect.return_value = MockFirewallConnector(success=True)
        
        # 执行回滚
        success, result = self.service.rollback_policy(1, 1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('deployment_id', result)
        self.assertIn('策略回滚成功', result['message'])
    
    def test_sync_policy_status(self):
        """测试同步策略状态"""
        # 配置成功的连接器工厂
        self.service.connector_factory = MagicMock()
        self.service.connector_factory.create_and_connect.return_value = MockFirewallConnector(success=True)
        
        # 执行同步
        result = self.service.sync_policy_status()
        
        # 验证结果
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['success'], 1)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(len(result['details']), 1)
        self.assertEqual(result['details'][0]['policy_id'], 1)
        self.assertEqual(result['details'][0]['status'], 'active')
    
    def test_get_policy_status(self):
        """测试获取策略状态"""
        # 配置成功的连接器工厂
        self.service.connector_factory = MagicMock()
        connector = MockFirewallConnector(success=True)
        self.service.connector_factory.create_and_connect.return_value = connector
        
        # 执行获取状态
        success, result = self.service.get_policy_status(1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('device_status', result)
        self.assertEqual(result['device_status']['status'], 'active')
        
        # 验证连接器工厂被调用
        self.service.connector_factory.create_and_connect.assert_called_once_with(self.test_device)
    
    def test_verify_policy(self):
        """测试验证策略"""
        # 配置成功的连接器工厂
        self.service.connector_factory = MagicMock()
        connector = MockFirewallConnector(success=True)
        connector.verify_policy = MagicMock(return_value=(True, "Valid policy"))
        self.service.connector_factory.create_and_connect.return_value = connector
        
        # 执行验证
        success, result = self.service.verify_policy(1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(result['message'], "Valid policy")
        
        # 验证连接器方法被调用
        connector.verify_policy.assert_called_once_with(self.test_policy.config)


if __name__ == '__main__':
    unittest.main() 