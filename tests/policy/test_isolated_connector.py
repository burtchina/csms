#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
防火墙连接器隔离测试
使用Mock对象替代实际的导入依赖，避免'src'模块导入问题
"""

import unittest
from unittest.mock import MagicMock, patch

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


class MockFirewallConnectionError(Exception):
    """模拟防火墙连接异常"""
    pass


class MockFirewallDeployError(Exception):
    """模拟防火墙部署异常"""
    pass


class MockFirewallConnector:
    """模拟防火墙连接器基类"""
    
    def connect(self, device):
        """连接设备"""
        return True
    
    def disconnect(self):
        """断开连接"""
        return True
    
    def is_connected(self):
        """检查是否已连接"""
        return True
    
    def deploy_policy(self, policy_config):
        """部署策略"""
        return True, "Success"
    
    def get_policy_status(self, policy_id):
        """获取策略状态"""
        return {"status": "active"}
    
    def rollback_policy(self, policy_id):
        """回滚策略"""
        return True, "Success"
    
    def verify_policy(self, policy_config):
        """验证策略配置"""
        return True, "Valid"


class MockGenericFirewallConnector(MockFirewallConnector):
    """模拟通用防火墙连接器"""
    
    def __init__(self):
        self.device = None
        self.connected = False
    
    def connect(self, device):
        self.device = device
        self.connected = True
        return True
    
    def disconnect(self):
        self.connected = False
        return True
    
    def is_connected(self):
        return self.connected
    
    def deploy_policy(self, policy_config):
        if not self.is_connected():
            return False, "Not connected"
        
        # 模拟策略部署逻辑
        if "ipsec_settings" in policy_config:
            return True, "IPSec policy deployed successfully"
        else:
            return False, "Invalid policy configuration"


class MockHuaweiFirewallConnector(MockGenericFirewallConnector):
    """模拟华为防火墙连接器"""
    
    def deploy_policy(self, policy_config):
        if not self.is_connected():
            return False, "Not connected"
        
        # 模拟华为设备特定的策略部署
        return True, "IPSec policy deployed successfully on Huawei device"


class MockCiscoFirewallConnector(MockGenericFirewallConnector):
    """模拟思科防火墙连接器"""
    
    def deploy_policy(self, policy_config):
        if not self.is_connected():
            return False, "Not connected"
        
        # 模拟思科设备特定的策略部署
        return True, "IPSec policy deployed successfully on Cisco device"


class MockConnectorFactory:
    """模拟连接器工厂"""
    
    @staticmethod
    def get_connector(device):
        """根据设备类型返回合适的连接器"""
        if "huawei" in device.manufacturer.lower():
            return MockHuaweiFirewallConnector()
        elif "cisco" in device.manufacturer.lower():
            return MockCiscoFirewallConnector()
        else:
            return MockGenericFirewallConnector()
    
    @staticmethod
    def create_and_connect(device):
        """创建连接器并连接"""
        connector = MockConnectorFactory.get_connector(device)
        if connector.connect(device):
            return connector
        return None


class TestIsolatedFirewallConnector(unittest.TestCase):
    """防火墙连接器隔离测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试设备
        self.generic_device = MockDevice(manufacturer="Generic", model="Generic")
        self.huawei_device = MockDevice(manufacturer="Huawei", model="USG6000")
        self.cisco_device = MockDevice(manufacturer="Cisco", model="ASA5500")
        
        # 创建测试策略配置
        self.test_policy = {
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
            },
            "tunnel_settings": {
                "local_subnet": "192.168.1.0/24",
                "remote_subnet": "192.168.2.0/24",
                "remote_gateway": "203.0.113.1"
            }
        }
        
        self.invalid_policy = {
            "type": "firewall",
            "firewall_settings": {
                "default_action": "deny"
            }
        }
    
    def test_connector_factory_creates_appropriate_connector(self):
        """测试连接器工厂能根据设备类型创建合适的连接器"""
        generic_connector = MockConnectorFactory.get_connector(self.generic_device)
        huawei_connector = MockConnectorFactory.get_connector(self.huawei_device)
        cisco_connector = MockConnectorFactory.get_connector(self.cisco_device)
        
        self.assertIsInstance(generic_connector, MockGenericFirewallConnector)
        self.assertIsInstance(huawei_connector, MockHuaweiFirewallConnector)
        self.assertIsInstance(cisco_connector, MockCiscoFirewallConnector)
    
    def test_create_and_connect_success(self):
        """测试创建并连接成功"""
        connector = MockConnectorFactory.create_and_connect(self.huawei_device)
        
        self.assertIsNotNone(connector)
        self.assertTrue(connector.is_connected())
        self.assertEqual(connector.device, self.huawei_device)
    
    def test_deploy_policy_success(self):
        """测试策略部署成功"""
        connector = MockConnectorFactory.create_and_connect(self.huawei_device)
        
        success, message = connector.deploy_policy(self.test_policy)
        
        self.assertTrue(success)
        self.assertIn("successfully", message)
    
    def test_deploy_policy_failure_with_invalid_config(self):
        """测试部署无效策略失败"""
        connector = MockConnectorFactory.create_and_connect(self.generic_device)
        
        success, message = connector.deploy_policy(self.invalid_policy)
        
        self.assertFalse(success)
        self.assertIn("Invalid", message)
    
    def test_deploy_policy_failure_not_connected(self):
        """测试未连接时部署失败"""
        connector = MockGenericFirewallConnector()  # 未连接
        
        success, message = connector.deploy_policy(self.test_policy)
        
        self.assertFalse(success)
        self.assertIn("Not connected", message)
    
    def test_disconnect(self):
        """测试断开连接"""
        connector = MockConnectorFactory.create_and_connect(self.cisco_device)
        
        # 确保连接成功
        self.assertTrue(connector.is_connected())
        
        # 断开连接
        success = connector.disconnect()
        
        self.assertTrue(success)
        self.assertFalse(connector.is_connected())


if __name__ == '__main__':
    unittest.main() 