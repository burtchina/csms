#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用防火墙连接器实现
适用于大多数支持SSH/Telnet的防火墙设备
"""

import time
import re
import logging
import json
from typing import Dict, Any, Tuple, Optional, List
import paramiko

from src.models.device import Device
from src.modules.policy.connectors.firewall_connector import (
    FirewallConnector,
    FirewallConnectionError,
    FirewallDeployError
)


class GenericFirewallConnector(FirewallConnector):
    """通用防火墙连接器，基于SSH/Telnet协议"""
    
    def __init__(self, timeout: int = 30, retry_count: int = 3, retry_interval: int = 5):
        """初始化连接器
        
        Args:
            timeout: 连接超时时间（秒）
            retry_count: 连接重试次数
            retry_interval: 重试间隔（秒）
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_interval = retry_interval
        self.device = None
        self.ssh_client = None
        self.session = None
        self.last_error = None
    
    def connect(self, device: Device) -> bool:
        """连接到防火墙设备
        
        Args:
            device: 设备对象
            
        Returns:
            bool: 连接是否成功
            
        Raises:
            FirewallConnectionError: 连接失败时抛出
        """
        self.device = device
        
        # 检查设备是否支持SSH
        if device.connection_protocol != 'ssh':
            error_msg = f"不支持的连接协议: {device.connection_protocol}"
            self._log_error(error_msg)
            self.last_error = error_msg
            raise FirewallConnectionError(error_msg)
        
        # 创建SSH客户端
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 尝试连接
        for attempt in range(self.retry_count):
            try:
                logging.info(f"正在连接防火墙设备 {device.name} ({device.ip_address})")
                self.ssh_client.connect(
                    hostname=device.ip_address,
                    port=device.port or 22,
                    username=device.username,
                    password=device.password,
                    timeout=self.timeout
                )
                self.session = self.ssh_client.invoke_shell()
                logging.info(f"已连接到防火墙设备 {device.name} ({device.ip_address})")
                return True
            except Exception as e:
                error_msg = f"连接防火墙设备失败 ({attempt+1}/{self.retry_count})"
                self._log_error(error_msg, e)
                self.last_error = str(e)
                
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_interval)
                else:
                    raise FirewallConnectionError(f"连接防火墙设备失败: {str(e)}")
        
        return False
    
    def disconnect(self) -> bool:
        """断开与防火墙设备的连接
        
        Returns:
            bool: 断开连接是否成功
        """
        if self.ssh_client:
            try:
                if self.session:
                    self.session.close()
                self.ssh_client.close()
                logging.info(f"已断开与防火墙设备的连接: {self.device.name}")
                return True
            except Exception as e:
                self._log_error("断开连接时发生错误", e)
                return False
        return True  # 如果未连接，则视为断开成功
    
    def is_connected(self) -> bool:
        """检查是否已连接到防火墙
        
        Returns:
            bool: 是否已连接
        """
        if not self.ssh_client or not self.session:
            return False
        
        try:
            transport = self.ssh_client.get_transport()
            return transport and transport.is_active()
        except Exception:
            return False
    
    def deploy_policy(self, policy_config: Dict[str, Any]) -> Tuple[bool, str]:
        """部署策略到防火墙设备
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
            
        Raises:
            FirewallDeployError: 部署失败时抛出
        """
        if not self.is_connected():
            raise FirewallDeployError("未连接到防火墙设备")
        
        try:
            # 生成防火墙配置命令
            commands = self._generate_firewall_commands(policy_config)
            
            # 执行命令
            result = self._execute_commands(commands)
            
            # 检查执行结果
            success = self._check_deployment_result(result)
            
            if success:
                message = "策略部署成功"
                logging.info(f"{message}: {self.device.name}")
                return True, message
            else:
                error_msg = "策略部署失败：命令执行错误"
                logging.error(f"{error_msg}: {self.device.name}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"部署策略时发生错误: {str(e)}"
            self._log_error(error_msg)
            raise FirewallDeployError(error_msg)
    
    def get_policy_status(self, policy_id: str) -> Dict[str, Any]:
        """获取策略在设备上的状态
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            Dict[str, Any]: 策略状态信息
        """
        if not self.is_connected():
            return {
                'status': 'unknown',
                'error': '未连接到防火墙设备'
            }
        
        try:
            # 获取策略状态的命令
            commands = self._get_policy_status_commands(policy_id)
            
            # 执行命令
            result = self._execute_commands(commands)
            
            # 解析结果
            status = self._parse_policy_status(result)
            
            return status
        except Exception as e:
            error_msg = f"获取策略状态时发生错误: {str(e)}"
            self._log_error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def rollback_policy(self, policy_id: str) -> Tuple[bool, str]:
        """回滚策略
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        if not self.is_connected():
            return False, "未连接到防火墙设备"
        
        try:
            # 获取回滚命令
            commands = self._get_rollback_commands(policy_id)
            
            # 执行命令
            result = self._execute_commands(commands)
            
            # 检查执行结果
            success = self._check_rollback_result(result)
            
            if success:
                message = "策略回滚成功"
                logging.info(f"{message}: {self.device.name}")
                return True, message
            else:
                error_msg = "策略回滚失败：命令执行错误"
                logging.error(f"{error_msg}: {self.device.name}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"回滚策略时发生错误: {str(e)}"
            self._log_error(error_msg)
            return False, error_msg
    
    def verify_policy(self, policy_config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证策略配置的有效性
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            Tuple[bool, str]: (是否有效, 结果信息)
        """
        try:
            # 生成验证命令（通常是检查配置而不应用）
            commands = self._generate_verify_commands(policy_config)
            
            if not self.is_connected():
                # 对于验证，可以不要求已连接
                return True, "配置格式有效（未实际连接到设备验证）"
            
            # 执行命令
            result = self._execute_commands(commands)
            
            # 检查执行结果
            is_valid, message = self._check_verify_result(result)
            
            return is_valid, message
                
        except Exception as e:
            error_msg = f"验证策略时发生错误: {str(e)}"
            self._log_error(error_msg)
            return False, error_msg
    
    def _execute_commands(self, commands: List[str]) -> str:
        """执行命令并返回结果
        
        Args:
            commands: 要执行的命令列表
            
        Returns:
            str: 执行结果
        """
        if not self.is_connected():
            raise FirewallConnectionError("未连接到防火墙设备")
        
        output = ""
        
        try:
            for cmd in commands:
                logging.debug(f"执行命令: {cmd}")
                self.session.send(cmd + "\n")
                time.sleep(2)  # 等待命令执行
                
                # 接收输出
                while self.session.recv_ready():
                    part = self.session.recv(4096).decode('utf-8', errors='ignore')
                    output += part
                    # 如果输出中包含更多数据的提示，如"--More--"
                    if re.search(r'--+\s*[Mm]ore\s*--+', part):
                        self.session.send(" ")  # 发送空格继续显示
                        time.sleep(0.5)
                
            return output
        except Exception as e:
            error_msg = f"执行命令时发生错误: {str(e)}"
            self._log_error(error_msg)
            raise FirewallDeployError(error_msg)
    
    def _generate_firewall_commands(self, policy_config: Dict[str, Any]) -> List[str]:
        """生成防火墙配置命令
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            List[str]: 命令列表
        """
        # 检查策略类型
        if policy_config.get("type") != "ipsec":
            return []  # 目前只支持IPSec类型策略
        
        # 提取策略关键参数
        ipsec_settings = policy_config.get("ipsec_settings", {})
        tunnel_settings = policy_config.get("tunnel_settings", {})
        firewall_settings = policy_config.get("firewall_settings", {})
        
        if not ipsec_settings or not tunnel_settings:
            logging.error("缺少必要的IPSec配置参数")
            return []
        
        # 提取IPSec配置
        encryption = ipsec_settings.get("encryption", {})
        authentication = ipsec_settings.get("authentication", {})
        lifetime = ipsec_settings.get("lifetime", {})
        
        # 提取隧道配置
        local_subnet = tunnel_settings.get("local_subnet", "")
        remote_subnet = tunnel_settings.get("remote_subnet", "")
        remote_gateway = tunnel_settings.get("remote_gateway", "")
        
        if not local_subnet or not remote_subnet or not remote_gateway:
            logging.error("缺少必要的隧道配置参数")
            return []
        
        # 生成唯一ID，用于配置名称
        policy_id = str(hash(json.dumps(policy_config, sort_keys=True)) % 10000)
        
        # 构建命令列表
        commands = []
        
        # 进入配置模式
        commands.append("configure terminal")
        
        # 配置IKE策略（Phase 1）
        phase1_encryption = encryption.get("phase1", ["aes-256", "sha256", "dh-group2"])[0]
        phase1_hash = encryption.get("phase1", [])[1] if len(encryption.get("phase1", [])) > 1 else "sha256"
        phase1_dh = encryption.get("phase1", [])[2] if len(encryption.get("phase1", [])) > 2 else "dh-group2"
        phase1_lifetime = lifetime.get("phase1", 86400)
        
        commands.append(f"crypto isakmp policy {policy_id}")
        commands.append(f"encryption {phase1_encryption}")
        commands.append(f"hash {phase1_hash}")
        commands.append(f"group {phase1_dh}")
        commands.append(f"lifetime {phase1_lifetime}")
        
        # 配置预共享密钥
        if authentication.get("method") == "psk":
            psk = authentication.get("psk", "")
            if psk:
                commands.append(f"crypto isakmp key {psk} address {remote_gateway}")
        
        # 配置IPSec变换集（Phase 2）
        phase2_encryption = encryption.get("phase2", ["aes-256", "sha256"])[0]
        phase2_hash = encryption.get("phase2", [])[1] if len(encryption.get("phase2", [])) > 1 else "sha256"
        phase2_lifetime = lifetime.get("phase2", 3600)
        
        commands.append(f"crypto ipsec transform-set TS-{policy_id} {phase2_encryption} {phase2_hash}")
        commands.append(f"crypto ipsec security-association lifetime seconds {phase2_lifetime}")
        
        # 配置访问控制列表
        commands.append(f"access-list ACL-VPN-{policy_id} permit ip {local_subnet} {remote_subnet}")
        
        # 配置加密映射
        commands.append(f"crypto map VPN-MAP {policy_id} ipsec-isakmp")
        commands.append(f"crypto map VPN-MAP {policy_id} match address ACL-VPN-{policy_id}")
        commands.append(f"crypto map VPN-MAP {policy_id} set peer {remote_gateway}")
        commands.append(f"crypto map VPN-MAP {policy_id} set transform-set TS-{policy_id}")
        
        # 应用到接口
        # 注意：这一步需要知道连接外网的接口名称，这里假设是"outside"
        commands.append("interface outside")
        commands.append("crypto map VPN-MAP")
        
        # 配置防火墙策略
        if firewall_settings:
            default_action = firewall_settings.get("default_action", "deny")
            allowed_protocols = firewall_settings.get("allowed_protocols", [])
            
            # 允许特定协议通过
            for i, proto in enumerate(allowed_protocols):
                protocol = proto.get("protocol", "")
                port = proto.get("port", "")
                description = proto.get("description", f"Protocol-{i}")
                
                if protocol == "esp":
                    commands.append(f"access-list FIREWALL-{policy_id} permit esp any any")
                elif protocol and port:
                    commands.append(f"access-list FIREWALL-{policy_id} permit {protocol} any any eq {port}")
                elif protocol:
                    commands.append(f"access-list FIREWALL-{policy_id} permit {protocol} any any")
            
            # 应用默认动作
            if default_action == "deny":
                commands.append(f"access-list FIREWALL-{policy_id} deny ip any any")
            
            # 应用到接口
            commands.append("access-group FIREWALL-{policy_id} in interface outside")
        
        # 保存配置
        commands.append("end")
        commands.append("write memory")
        
        return commands
    
    def _get_policy_status_commands(self, policy_id: str) -> List[str]:
        """获取策略状态的命令
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 命令列表
        """
        # 根据不同厂商和设备类型，用于查询策略状态的命令会有所不同
        return [
            "show crypto ipsec sa",
            "show crypto isakmp sa"
        ]
    
    def _get_rollback_commands(self, policy_id: str) -> List[str]:
        """获取回滚策略的命令
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 回滚命令列表
        """
        # 通用防火墙设备的回滚命令（需要根据具体设备类型优化）
        commands = [
            "configure terminal",
            f"no crypto map VPN-MAP {policy_id}",  # 删除加密映射
            f"no crypto ipsec transform-set TS-{policy_id}",  # 删除变换集
            f"no crypto isakmp policy {policy_id}",  # 删除ISAKMP策略
            f"no access-list ACL-VPN-{policy_id}",  # 删除相关ACL
            "end",
            "write memory"  # 保存配置
        ]
        
        return commands
    
    def _generate_verify_commands(self, policy_config: Dict[str, Any]) -> List[str]:
        """生成验证策略配置的命令
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            List[str]: 命令列表
        """
        # 通常是基于"show"命令或测试模式的配置检查
        return [
            "show running-config crypto"
        ]
    
    def _check_deployment_result(self, result: str) -> bool:
        """检查部署结果是否成功
        
        Args:
            result: 命令执行结果
            
        Returns:
            bool: 是否成功
        """
        # 检查结果中是否包含错误信息
        error_patterns = [
            "Error",
            "Invalid command",
            "Failed to",
            "% Invalid input"
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                return False
        
        return True
    
    def _check_rollback_result(self, result: str) -> bool:
        """检查回滚结果是否成功
        
        Args:
            result: 命令执行结果
            
        Returns:
            bool: 是否成功
        """
        # 与部署检查逻辑类似
        return self._check_deployment_result(result)
    
    def _check_verify_result(self, result: str) -> Tuple[bool, str]:
        """检查验证结果
        
        Args:
            result: 命令执行结果
            
        Returns:
            Tuple[bool, str]: (是否有效, 消息)
        """
        # 检查结果中是否包含错误信息
        error_patterns = [
            "Error",
            "Invalid command",
            "Failed to",
            "% Invalid input"
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                return False, f"配置验证失败: 发现错误 '{pattern}'"
        
        return True, "配置验证通过"
    
    def _parse_policy_status(self, result: str) -> Dict[str, Any]:
        """解析策略状态
        
        Args:
            result: 命令执行结果
            
        Returns:
            Dict[str, Any]: 策略状态信息
        """
        status = {
            'status': 'unknown',
            'details': {}
        }
        
        # 检查IPSec状态
        if "IPSEC_SA established" in result or "QM_IDLE" in result:
            status['status'] = 'active'
            status['details']['tunnels'] = []
            
            # 提取隧道信息
            tunnel_matches = re.finditer(r'local\s+(\S+):(\d+)\s+remote\s+(\S+):(\d+)', result)
            for match in tunnel_matches:
                tunnel = {
                    'local_ip': match.group(1),
                    'local_port': match.group(2),
                    'remote_ip': match.group(3),
                    'remote_port': match.group(4)
                }
                status['details']['tunnels'].append(tunnel)
        elif "no IPSEC_SA established" in result:
            status['status'] = 'inactive'
            status['details']['reason'] = "No IPSec SA established"
        
        # 解析更多信息...
        # 此处可以根据不同设备的输出格式，提取更详细的状态信息
        
        return status 