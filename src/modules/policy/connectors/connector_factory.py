#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
防火墙连接器工厂
根据设备类型和厂商动态选择合适的连接器实现
"""

import logging
from typing import Optional

from src.models.device import Device
from src.modules.policy.connectors.firewall_connector import FirewallConnector
from src.modules.policy.connectors.generic_connector import GenericFirewallConnector
from src.modules.policy.connectors.huawei_connector import HuaweiFirewallConnector
from src.modules.policy.connectors.cisco_connector import CiscoFirewallConnector


class ConnectorFactory:
    """防火墙连接器工厂类"""
    
    @staticmethod
    def get_connector(device: Device) -> FirewallConnector:
        """根据设备类型获取合适的连接器
        
        Args:
            device: 设备对象
            
        Returns:
            FirewallConnector: 连接器实例
        """
        # 获取设备厂商信息
        manufacturer = device.manufacturer.lower() if device.manufacturer else ""
        model = device.model.lower() if device.model else ""
        
        # 根据厂商和型号选择合适的连接器
        if "huawei" in manufacturer or "hw" in manufacturer:
            logging.info(f"为设备 {device.name} 选择华为防火墙连接器")
            return HuaweiFirewallConnector()
        
        elif "cisco" in manufacturer or "asa" in model:
            logging.info(f"为设备 {device.name} 选择思科防火墙连接器")
            return CiscoFirewallConnector()
        
        # 默认使用通用连接器
        logging.info(f"为设备 {device.name} 选择通用防火墙连接器")
        return GenericFirewallConnector()
    
    @staticmethod
    def create_and_connect(device: Device) -> Optional[FirewallConnector]:
        """创建连接器并自动连接到设备
        
        Args:
            device: 设备对象
            
        Returns:
            Optional[FirewallConnector]: 已连接的连接器实例，连接失败则返回None
        """
        try:
            # 获取合适的连接器
            connector = ConnectorFactory.get_connector(device)
            
            # 连接到设备
            success = connector.connect(device)
            
            if success:
                return connector
            else:
                logging.error(f"连接设备 {device.name} 失败")
                return None
                
        except Exception as e:
            logging.error(f"创建连接器并连接设备 {device.name} 时发生错误: {str(e)}")
            return None 