#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
防火墙连接器抽象基类
定义与防火墙设备交互的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import logging

from src.models.device import Device


class FirewallConnectionError(Exception):
    """防火墙连接异常"""
    pass


class FirewallDeployError(Exception):
    """策略部署异常"""
    pass


class FirewallConnector(ABC):
    """防火墙连接器抽象基类"""
    
    @abstractmethod
    def connect(self, device: Device) -> bool:
        """连接到防火墙设备
        
        Args:
            device: 设备对象
            
        Returns:
            bool: 连接是否成功
            
        Raises:
            FirewallConnectionError: 连接失败时抛出
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开与防火墙设备的连接
        
        Returns:
            bool: 断开连接是否成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接到防火墙
        
        Returns:
            bool: 是否已连接
        """
        pass
    
    @abstractmethod
    def deploy_policy(self, policy_config: Dict[str, Any]) -> Tuple[bool, str]:
        """部署策略到防火墙设备
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
            
        Raises:
            FirewallDeployError: 部署失败时抛出
        """
        pass
    
    @abstractmethod
    def get_policy_status(self, policy_id: str) -> Dict[str, Any]:
        """获取策略在设备上的状态
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            Dict[str, Any]: 策略状态信息
        """
        pass
    
    @abstractmethod
    def rollback_policy(self, policy_id: str) -> Tuple[bool, str]:
        """回滚策略
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        pass
    
    @abstractmethod
    def verify_policy(self, policy_config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证策略配置的有效性
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            Tuple[bool, str]: (是否有效, 结果信息)
        """
        pass
    
    def _log_error(self, message: str, exception: Optional[Exception] = None) -> None:
        """记录错误日志
        
        Args:
            message: 错误信息
            exception: 异常对象
        """
        error_msg = message
        if exception:
            error_msg += f" 异常详情: {str(exception)}"
        
        logging.error(error_msg) 