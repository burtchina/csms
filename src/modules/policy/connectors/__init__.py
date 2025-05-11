#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
防火墙连接器模块
提供与不同厂商防火墙设备通信的接口
"""

from src.modules.policy.connectors.firewall_connector import (
    FirewallConnector,
    FirewallConnectionError,
    FirewallDeployError
)
from src.modules.policy.connectors.generic_connector import GenericFirewallConnector
from src.modules.policy.connectors.huawei_connector import HuaweiFirewallConnector
from src.modules.policy.connectors.cisco_connector import CiscoFirewallConnector
from src.modules.policy.connectors.connector_factory import ConnectorFactory

# 导出公共接口
__all__ = [
    'FirewallConnector',
    'FirewallConnectionError',
    'FirewallDeployError',
    'HuaweiFirewallConnector',
    'CiscoFirewallConnector',
    'GenericFirewallConnector',
    'ConnectorFactory',
] 