#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略下发服务单元测试
"""

import unittest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.modules.policy.services.policy_deploy_service import PolicyDeployService
from src.modules.policy.connectors.firewall_connector import FirewallConnectionError


class TestPolicyDeployService(unittest.TestCase):
    """策略下发服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟对象
        self.mock_policy_repo = MagicMock()
        self.mock_deployment_repo = MagicMock()
        self.mock_device = MagicMock()
        self.mock_policy = MagicMock()
        self.mock_connector = MagicMock()
        
        # 配置模拟策略
        self.mock_policy.id = 1
        self.mock_policy.name = "Test Policy"
        self.mock_policy.status = "active"
        self.mock_policy.config = {
            "type": "ipsec",
            "ipsec_settings": {
                "encryption": {
                    "phase1": ["aes-256", "sha256", "dh-group14"],
                    "phase2": ["aes-256", "sha256"]
                }
            },
            "tunnel_settings": {
                "local_subnet": "192.168.1.0/24",
                "remote_subnet": "192.168.2.0/24",
                "remote_gateway": "203.0.113.1"
            }
        }
        
        # 配置模拟设备
        self.mock_device.id = 1
        self.mock_device.name = "Test Firewall"
        self.mock_device.ip_address = "192.168.1.1"
        
        # 配置模拟部署记录
        self.mock_deployment = MagicMock()
        self.mock_deployment.id = 1
        self.mock_deployment.policy_id = 1
        self.mock_deployment.device_id = 1
        self.mock_deployment.status = "success"
        self.mock_deployment.config_snapshot = self.mock_policy.config
        
        # 配置模拟工厂和连接器
        self.mock_connector.deploy_policy.return_value = (True, "策略部署成功")
        self.mock_connector.get_policy_status.return_value = {"status": "active"}
        self.mock_connector.rollback_policy.return_value = (True, "策略回滚成功")
        
        # 初始化服务实例
        self.deploy_service = PolicyDeployService()
        self.deploy_service.policy_repo = self.mock_policy_repo
        self.deploy_service.deployment_repo = self.mock_deployment_repo
        
        # 配置仓库方法返回值
        self.mock_policy_repo.get_by_id.return_value = self.mock_policy
        self.mock_deployment_repo.create.return_value = self.mock_deployment
        self.mock_deployment_repo.get_latest_deployment.return_value = self.mock_deployment
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_deploy_policy_success(self, mock_factory, mock_device_model):
        """测试成功部署策略"""
        # 配置模拟
        mock_device_model.query.get.return_value = self.mock_device
        mock_factory.create_and_connect.return_value = self.mock_connector
        
        # 执行测试
        success, result = self.deploy_service.deploy_policy(1, 1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('message', result)
        self.assertIn('deployment_id', result)
        self.assertEqual(result['deployment_id'], 1)
        
        # 验证调用
        self.mock_policy_repo.get_by_id.assert_called_once_with(1)
        mock_device_model.query.get.assert_called_once_with(1)
        self.mock_deployment_repo.create.assert_called_once()
        mock_factory.create_and_connect.assert_called_once_with(self.mock_device)
        self.mock_connector.deploy_policy.assert_called_once_with(self.mock_policy.config)
        self.mock_connector.disconnect.assert_called_once()
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_deploy_policy_device_not_found(self, mock_factory, mock_device_model):
        """测试设备不存在的情况"""
        # 配置模拟
        mock_device_model.query.get.return_value = None
        
        # 执行测试
        success, result = self.deploy_service.deploy_policy(1, 1, 1)
        
        # 验证结果
        self.assertFalse(success)
        self.assertIn('error', result)
        self.assertEqual(result['error'], '设备不存在')
        
        # 验证未创建部署记录
        self.mock_deployment_repo.create.assert_not_called()
        mock_factory.create_and_connect.assert_not_called()
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_deploy_policy_connection_error(self, mock_factory, mock_device_model):
        """测试连接失败的情况"""
        # 配置模拟
        mock_device_model.query.get.return_value = self.mock_device
        mock_factory.create_and_connect.return_value = None
        
        # 执行测试
        success, result = self.deploy_service.deploy_policy(1, 1, 1)
        
        # 验证结果
        self.assertFalse(success)
        self.assertIn('error', result)
        self.assertIn('deployment_id', result)
        
        # 验证部署记录已更新为失败状态
        self.mock_deployment_repo.update.assert_called_once()
        update_args = self.mock_deployment_repo.update.call_args[0]
        self.assertEqual(update_args[0], 1)  # deployment_id
        self.assertEqual(update_args[1]['status'], 'failed')
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_get_policy_status(self, mock_factory, mock_device_model):
        """测试获取策略状态"""
        # 配置模拟
        mock_device_model.query.get.return_value = self.mock_device
        mock_factory.create_and_connect.return_value = self.mock_connector
        
        # 执行测试
        success, result = self.deploy_service.get_policy_status(1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('device_status', result)
        self.assertEqual(result['device_status']['status'], 'active')
        
        # 验证调用
        self.mock_deployment_repo.get_latest_deployment.assert_called_once_with(1, 1)
        mock_factory.create_and_connect.assert_called_once_with(self.mock_device)
        self.mock_connector.get_policy_status.assert_called_once_with('1')
        self.mock_connector.disconnect.assert_called_once()
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_rollback_policy(self, mock_factory, mock_device_model):
        """测试回滚策略"""
        # 配置模拟
        mock_device_model.query.get.return_value = self.mock_device
        mock_factory.create_and_connect.return_value = self.mock_connector
        
        # 执行测试
        success, result = self.deploy_service.rollback_policy(1, 1, 1)
        
        # 验证结果
        self.assertTrue(success)
        self.assertIn('message', result)
        self.assertEqual(result['message'], '策略回滚成功: 策略回滚成功')
        
        # 验证调用
        self.mock_deployment_repo.get_latest_deployment.assert_called_once_with(1, 1)
        mock_factory.create_and_connect.assert_called_once_with(self.mock_device)
        self.mock_connector.rollback_policy.assert_called_once_with('1')
        self.mock_connector.disconnect.assert_called_once()
    
    @patch('src.modules.policy.services.policy_deploy_service.Device')
    @patch('src.modules.policy.services.policy_deploy_service.ConnectorFactory')
    def test_sync_policy_status(self, mock_factory, mock_device_model):
        """测试同步策略状态"""
        # 配置模拟
        mock_device_model.query.get.return_value = self.mock_device
        mock_factory.create_and_connect.return_value = self.mock_connector
        self.mock_deployment_repo.get_all.return_value = [self.mock_deployment]
        
        # 执行测试
        result = self.deploy_service.sync_policy_status()
        
        # 验证结果
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['success'], 1)
        self.assertEqual(result['failed'], 0)
        self.assertEqual(len(result['details']), 1)
        
        # 验证调用
        self.mock_deployment_repo.get_all.assert_called_once()
        mock_factory.create_and_connect.assert_called_once_with(self.mock_device)
        self.mock_connector.get_policy_status.assert_called_once_with('1')
        self.mock_connector.disconnect.assert_called_once()


if __name__ == '__main__':
    unittest.main() 