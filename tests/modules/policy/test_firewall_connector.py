#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
防火墙连接器单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from src.models.device import Device
from src.modules.policy.connectors.generic_connector import GenericFirewallConnector
from src.modules.policy.connectors.huawei_connector import HuaweiFirewallConnector
from src.modules.policy.connectors.cisco_connector import CiscoFirewallConnector
from src.modules.policy.connectors.connector_factory import ConnectorFactory
from src.modules.policy.connectors.firewall_connector import FirewallConnectionError, FirewallDeployError


class TestFirewallConnector(unittest.TestCase):
    """防火墙连接器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟设备
        self.mock_device = MagicMock(spec=Device)
        self.mock_device.id = 1
        self.mock_device.name = "Test Firewall"
        self.mock_device.ip_address = "192.168.1.1"
        self.mock_device.port = 22
        self.mock_device.username = "admin"
        self.mock_device.password = "admin123"
        self.mock_device.connection_protocol = "ssh"
        
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
            },
            "firewall_settings": {
                "default_action": "deny",
                "allowed_protocols": [
                    {"protocol": "esp"},
                    {"protocol": "udp", "port": 500, "description": "IKE"},
                    {"protocol": "udp", "port": 4500, "description": "NAT-T"}
                ]
            }
        }
    
    @patch('src.modules.policy.connectors.generic_connector.paramiko.SSHClient')
    def test_generic_connector_connect(self, mock_ssh):
        """测试通用连接器的连接功能"""
        # 配置模拟
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        
        mock_client = MagicMock()
        mock_client.get_transport.return_value = mock_transport
        
        mock_ssh.return_value = mock_client
        
        # 创建连接器
        connector = GenericFirewallConnector()
        
        # 连接
        result = connector.connect(self.mock_device)
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(connector.is_connected())
        
        # 验证调用
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname=self.mock_device.ip_address,
            port=self.mock_device.port,
            username=self.mock_device.username,
            password=self.mock_device.password,
            timeout=30
        )
    
    @patch('src.modules.policy.connectors.generic_connector.paramiko.SSHClient')
    def test_generic_connector_disconnect(self, mock_ssh):
        """测试通用连接器的断开连接功能"""
        # 配置模拟
        mock_session = MagicMock()
        mock_client = MagicMock()
        
        mock_ssh.return_value = mock_client
        
        # 创建连接器
        connector = GenericFirewallConnector()
        connector.ssh_client = mock_client
        connector.session = mock_session
        connector.device = self.mock_device
        
        # 断开连接
        result = connector.disconnect()
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证调用
        mock_session.close.assert_called_once()
        mock_client.close.assert_called_once()
    
    @patch('src.modules.policy.connectors.generic_connector.GenericFirewallConnector._execute_commands')
    @patch('src.modules.policy.connectors.generic_connector.GenericFirewallConnector._generate_firewall_commands')
    def test_generic_connector_deploy_policy(self, mock_generate, mock_execute):
        """测试通用连接器的策略部署功能"""
        # 配置模拟
        mock_generate.return_value = ["command1", "command2"]
        mock_execute.return_value = "Command executed successfully"
        
        # 创建连接器
        connector = GenericFirewallConnector()
        connector.is_connected = MagicMock(return_value=True)
        
        # 部署策略
        success, message = connector.deploy_policy(self.test_policy)
        
        # 验证结果
        self.assertTrue(success)
        
        # 验证调用
        mock_generate.assert_called_once_with(self.test_policy)
        mock_execute.assert_called_once_with(["command1", "command2"])
    
    @patch('src.modules.policy.connectors.generic_connector.GenericFirewallConnector._execute_commands')
    @patch('src.modules.policy.connectors.generic_connector.GenericFirewallConnector._get_policy_status_commands')
    def test_generic_connector_get_policy_status(self, mock_commands, mock_execute):
        """测试通用连接器的策略状态获取功能"""
        # 配置模拟
        mock_commands.return_value = ["status_command1", "status_command2"]
        mock_execute.return_value = "IPSEC_SA established"
        
        # 创建连接器
        connector = GenericFirewallConnector()
        connector.is_connected = MagicMock(return_value=True)
        
        # 获取策略状态
        status = connector.get_policy_status("1")
        
        # 验证结果
        self.assertEqual(status['status'], 'active')
        
        # 验证调用
        mock_commands.assert_called_once_with("1")
        mock_execute.assert_called_once_with(["status_command1", "status_command2"])
    
    def test_connector_factory(self):
        """测试连接器工厂"""
        # 配置华为设备
        huawei_device = MagicMock(spec=Device)
        huawei_device.manufacturer = "Huawei"
        huawei_device.model = "USG6000"
        
        # 配置思科设备
        cisco_device = MagicMock(spec=Device)
        cisco_device.manufacturer = "Cisco"
        cisco_device.model = "ASA5500"
        
        # 配置通用设备
        generic_device = MagicMock(spec=Device)
        generic_device.manufacturer = "Unknown"
        generic_device.model = "Generic"
        
        # 测试工厂根据设备类型创建不同的连接器
        huawei_connector = ConnectorFactory.get_connector(huawei_device)
        cisco_connector = ConnectorFactory.get_connector(cisco_device)
        generic_connector = ConnectorFactory.get_connector(generic_device)
        
        # 验证结果
        self.assertIsInstance(huawei_connector, HuaweiFirewallConnector)
        self.assertIsInstance(cisco_connector, CiscoFirewallConnector)
        self.assertIsInstance(generic_connector, GenericFirewallConnector)
    
    @patch('src.modules.policy.connectors.huawei_connector.HuaweiFirewallConnector.connect')
    def test_huawei_connector_commands(self, mock_connect):
        """测试华为连接器生成的命令"""
        # 创建连接器
        connector = HuaweiFirewallConnector()
        
        # 生成命令
        commands = connector._generate_firewall_commands(self.test_policy)
        
        # 验证命令包含华为特定语法
        self.assertTrue(any("system-view" in cmd for cmd in commands))
        self.assertTrue(any("ike proposal" in cmd for cmd in commands))
        self.assertTrue(any("ipsec proposal" in cmd for cmd in commands))
        self.assertTrue(any("acl" in cmd for cmd in commands))
    
    @patch('src.modules.policy.connectors.cisco_connector.CiscoFirewallConnector.connect')
    def test_cisco_connector_commands(self, mock_connect):
        """测试思科连接器生成的命令"""
        # 创建连接器
        connector = CiscoFirewallConnector()
        
        # 生成命令
        commands = connector._generate_firewall_commands(self.test_policy)
        
        # 验证命令包含思科特定语法
        self.assertTrue(any("conf t" in cmd for cmd in commands))
        self.assertTrue(any("crypto isakmp policy" in cmd for cmd in commands))
        self.assertTrue(any("crypto ipsec transform-set" in cmd for cmd in commands))
        self.assertTrue(any("access-list" in cmd for cmd in commands))
    
    @patch('src.modules.policy.connectors.connector_factory.ConnectorFactory.get_connector')
    def test_create_and_connect(self, mock_get_connector):
        """测试创建并连接功能"""
        # 配置模拟
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_get_connector.return_value = mock_connector
        
        # 创建并连接
        result = ConnectorFactory.create_and_connect(self.mock_device)
        
        # 验证结果
        self.assertEqual(result, mock_connector)
        
        # 验证调用
        mock_get_connector.assert_called_once_with(self.mock_device)
        mock_connector.connect.assert_called_once_with(self.mock_device)
    
    @patch('src.modules.policy.connectors.connector_factory.ConnectorFactory.get_connector')
    def test_create_and_connect_failure(self, mock_get_connector):
        """测试连接失败情况"""
        # 配置模拟
        mock_connector = MagicMock()
        mock_connector.connect.return_value = False
        mock_get_connector.return_value = mock_connector
        
        # 创建并连接
        result = ConnectorFactory.create_and_connect(self.mock_device)
        
        # 验证结果
        self.assertIsNone(result)
        
        # 验证调用
        mock_get_connector.assert_called_once_with(self.mock_device)
        mock_connector.connect.assert_called_once_with(self.mock_device)


if __name__ == '__main__':
    unittest.main() 