#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 设备连接器模块
"""

import time
import socket
import logging
from abc import ABC, abstractmethod

import paramiko
from netmiko import ConnectHandler
from pysnmp.hlapi import *

logger = logging.getLogger(__name__)

class DeviceConnector(ABC):
    """设备连接器基类"""
    
    def __init__(self, ip, username=None, password=None, timeout=5):
        """
        初始化连接器
        
        Args:
            ip: 设备IP地址
            username: 用户名
            password: 密码
            timeout: 超时时间（秒）
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self._connected = False
    
    @abstractmethod
    def connect(self):
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    def is_connected(self):
        """检查是否已连接"""
        return self._connected
    
    def check_connectivity(self):
        """检查设备连通性"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.ip, 22))  # 默认检查SSH端口
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"Connectivity check failed for {self.ip}: {str(e)}")
            return False


class SSHConnector(DeviceConnector):
    """SSH连接器"""
    
    def __init__(self, ip, username, password, timeout=5):
        """初始化SSH连接器"""
        super().__init__(ip, username, password, timeout)
        self.client = None
    
    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.ip,
                username=self.username,
                password=self.password,
                timeout=self.timeout
            )
            self._connected = True
            logger.info(f"SSH connection established with {self.ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to establish SSH connection with {self.ip}: {str(e)}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info(f"SSH connection closed with {self.ip}")
    
    def execute_command(self, command):
        """
        执行SSH命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            命令输出结果
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Command '{command}' on {self.ip} returned error: {error}")
            
            return output
        except Exception as e:
            logger.error(f"Failed to execute command '{command}' on {self.ip}: {str(e)}")
            self._connected = False
            return None
    
    def execute_commands(self, commands):
        """
        执行多个SSH命令
        
        Args:
            commands: 命令列表
            
        Returns:
            命令输出结果列表
        """
        results = []
        for command in commands:
            result = self.execute_command(command)
            results.append(result)
        return results


class NetmikoConnector(DeviceConnector):
    """Netmiko连接器"""
    
    def __init__(self, ip, username, password, device_type='huawei', enable_password=None, timeout=5):
        """初始化Netmiko连接器"""
        super().__init__(ip, username, password, timeout)
        self.device_type = device_type
        self.enable_password = enable_password or password
        self.connection = None
    
    def connect(self):
        """建立Netmiko连接"""
        try:
            device = {
                'device_type': self.device_type,
                'ip': self.ip,
                'username': self.username,
                'password': self.password,
                'secret': self.enable_password,
                'timeout': self.timeout
            }
            self.connection = ConnectHandler(**device)
            self._connected = True
            logger.info(f"Netmiko connection established with {self.ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to establish Netmiko connection with {self.ip}: {str(e)}")
            self._connected = False
            return False
    
    def disconnect(self):
        """断开Netmiko连接"""
        if self.connection:
            self.connection.disconnect()
            self._connected = False
            logger.info(f"Netmiko connection closed with {self.ip}")
    
    def execute_command(self, command, enable=False):
        """
        执行Netmiko命令
        
        Args:
            command: 要执行的命令
            enable: 是否进入特权模式
            
        Returns:
            命令输出结果
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            if enable and not self.connection.check_enable_mode():
                self.connection.enable()
            
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            logger.error(f"Failed to execute command '{command}' on {self.ip}: {str(e)}")
            self._connected = False
            return None
    
    def execute_config(self, config_commands):
        """
        执行配置命令
        
        Args:
            config_commands: 配置命令列表
            
        Returns:
            命令输出结果
        """
        if not self.is_connected():
            if not self.connect():
                return None
        
        try:
            output = self.connection.send_config_set(config_commands)
            return output
        except Exception as e:
            logger.error(f"Failed to execute config commands on {self.ip}: {str(e)}")
            self._connected = False
            return None


class SNMPConnector(DeviceConnector):
    """SNMP连接器"""
    
    def __init__(self, ip, community='public', version=2, timeout=5):
        """初始化SNMP连接器"""
        super().__init__(ip, timeout=timeout)
        self.community = community
        self.version = version
        self.port = 161
    
    def connect(self):
        """SNMP无需显式连接"""
        self._connected = True
        return True
    
    def disconnect(self):
        """SNMP无需显式断开连接"""
        self._connected = False
    
    def get(self, oid):
        """
        获取SNMP数据
        
        Args:
            oid: OID标识符
            
        Returns:
            查询结果
        """
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                       CommunityData(self.community, mpModel=0 if self.version == 1 else 1),
                       UdpTransportTarget((self.ip, self.port), timeout=self.timeout),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )
            
            if error_indication:
                logger.error(f"SNMP error for {self.ip}: {error_indication}")
                return None
            elif error_status:
                logger.error(f"SNMP error for {self.ip}: {error_status.prettyPrint()} at {var_binds[int(error_index) - 1][0] if error_index else '?'}")
                return None
            else:
                for var_bind in var_binds:
                    return var_bind[1].prettyPrint()
        except Exception as e:
            logger.error(f"Failed to get SNMP data from {self.ip}: {str(e)}")
            return None
    
    def get_bulk(self, oids):
        """
        批量获取SNMP数据
        
        Args:
            oids: OID列表
            
        Returns:
            查询结果字典
        """
        results = {}
        for oid in oids:
            result = self.get(oid)
            results[oid] = result
        return results
    
    def walk(self, oid):
        """
        SNMP遍历
        
        Args:
            oid: OID标识符
            
        Returns:
            遍历结果列表
        """
        results = []
        try:
            for error_indication, error_status, error_index, var_binds in nextCmd(
                    SnmpEngine(),
                    CommunityData(self.community, mpModel=0 if self.version == 1 else 1),
                    UdpTransportTarget((self.ip, self.port), timeout=self.timeout),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False
            ):
                if error_indication:
                    logger.error(f"SNMP error for {self.ip}: {error_indication}")
                    break
                elif error_status:
                    logger.error(f"SNMP error for {self.ip}: {error_status.prettyPrint()} at {var_binds[int(error_index) - 1][0] if error_index else '?'}")
                    break
                else:
                    for var_bind in var_binds:
                        results.append((var_bind[0].prettyPrint(), var_bind[1].prettyPrint()))
            return results
        except Exception as e:
            logger.error(f"Failed to walk SNMP data from {self.ip}: {str(e)}")
            return None


class TelnetConnector(DeviceConnector):
    """Telnet连接器"""
    
    def __init__(self, ip, username, password, enable_password=None, timeout=5):
        """初始化Telnet连接器"""
        super().__init__(ip, username, password, timeout)
        self.enable_password = enable_password or password
        # 使用Netmiko作为底层实现
        self.netmiko = NetmikoConnector(
            ip=ip, 
            username=username, 
            password=password, 
            device_type='huawei_telnet',  # 使用telnet设备类型
            enable_password=enable_password,
            timeout=timeout
        )
    
    def connect(self):
        """建立Telnet连接"""
        result = self.netmiko.connect()
        self._connected = result
        return result
    
    def disconnect(self):
        """断开Telnet连接"""
        self.netmiko.disconnect()
        self._connected = False
    
    def execute_command(self, command, enable=False):
        """
        执行Telnet命令
        
        Args:
            command: 要执行的命令
            enable: 是否进入特权模式
            
        Returns:
            命令输出结果
        """
        return self.netmiko.execute_command(command, enable)
    
    def execute_commands(self, commands, enable=False):
        """
        执行多个Telnet命令
        
        Args:
            commands: 命令列表
            enable: 是否进入特权模式
            
        Returns:
            命令输出结果列表
        """
        results = []
        for command in commands:
            result = self.execute_command(command, enable)
            results.append(result)
        return results


class DeviceConnectorFactory:
    """设备连接器工厂"""
    
    @staticmethod
    def create_connector(protocol, ip, **kwargs):
        """
        创建设备连接器
        
        Args:
            protocol: 通信协议（ssh, telnet, snmp）
            ip: 设备IP地址
            **kwargs: 其他参数
            
        Returns:
            设备连接器实例
        """
        if protocol.lower() == 'ssh':
            return SSHConnector(ip, **kwargs)
        elif protocol.lower() == 'telnet':
            return TelnetConnector(ip, **kwargs)
        elif protocol.lower() == 'snmp':
            return SNMPConnector(ip, **kwargs)
        elif protocol.lower() == 'netmiko':
            return NetmikoConnector(ip, **kwargs)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}") 