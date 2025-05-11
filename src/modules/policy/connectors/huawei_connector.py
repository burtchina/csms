#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
华为防火墙连接器实现
适用于华为USG系列防火墙设备
"""

import re
import logging
from typing import Dict, Any, Tuple, List

from src.modules.policy.connectors.generic_connector import GenericFirewallConnector


class HuaweiFirewallConnector(GenericFirewallConnector):
    """华为防火墙连接器，继承自通用连接器，针对华为设备进行定制"""
    
    def __init__(self, timeout: int = 30, retry_count: int = 3, retry_interval: int = 5):
        """初始化连接器
        
        Args:
            timeout: 连接超时时间（秒）
            retry_count: 连接重试次数
            retry_interval: 重试间隔（秒）
        """
        super().__init__(timeout, retry_count, retry_interval)
    
    def _generate_firewall_commands(self, policy_config: Dict[str, Any]) -> List[str]:
        """根据策略配置生成华为防火墙命令
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            List[str]: 命令列表
        """
        commands = []
        
        # 进入系统视图
        commands.append("system-view")
        
        # 处理IPSec策略配置
        if policy_config.get('type') == 'ipsec':
            ipsec_settings = policy_config.get('ipsec_settings', {})
            firewall_settings = policy_config.get('firewall_settings', {})
            tunnel_settings = policy_config.get('tunnel_settings', {})
            
            # 配置安全提议
            if ipsec_settings:
                # 提取加密算法
                phase1_algos = ipsec_settings.get('encryption', {}).get('phase1', [])
                phase2_algos = ipsec_settings.get('encryption', {}).get('phase2', [])
                
                # IKE提议配置
                commands.append("ike proposal 10")
                
                if phase1_algos:
                    # 设置加密算法（默认AES-256）
                    if 'aes-256' in phase1_algos:
                        commands.append("encryption-algorithm aes-256")
                    elif 'aes-128' in phase1_algos:
                        commands.append("encryption-algorithm aes-128")
                    elif 'des' in phase1_algos:
                        commands.append("encryption-algorithm des")
                    
                    # 设置认证算法（默认SHA256）
                    if 'sha256' in phase1_algos:
                        commands.append("authentication-algorithm sha2-256")
                    elif 'sha1' in phase1_algos:
                        commands.append("authentication-algorithm sha1")
                    elif 'md5' in phase1_algos:
                        commands.append("authentication-algorithm md5")
                    
                    # 设置DH组（默认group14）
                    if 'dh-group14' in phase1_algos:
                        commands.append("dh group14")
                    elif 'dh-group5' in phase1_algos:
                        commands.append("dh group5")
                    elif 'dh-group2' in phase1_algos:
                        commands.append("dh group2")
                else:
                    # 使用默认安全设置
                    commands.append("encryption-algorithm aes-256")
                    commands.append("authentication-algorithm sha2-256")
                    commands.append("dh group14")
                
                # 设置IKE策略生存周期
                lifetime = ipsec_settings.get('lifetime', {}).get('phase1', 86400)
                commands.append(f"sa duration {lifetime}")
                commands.append("quit")
                
                # 配置IPSec安全提议
                commands.append("ipsec proposal ipsec-prop1")
                
                if phase2_algos:
                    # 设置加密算法（默认AES-256）
                    if 'aes-256' in phase2_algos:
                        commands.append("esp encryption-algorithm aes-256")
                    elif 'aes-128' in phase2_algos:
                        commands.append("esp encryption-algorithm aes-128")
                    elif 'des' in phase2_algos:
                        commands.append("esp encryption-algorithm des")
                    
                    # 设置认证算法（默认SHA256）
                    if 'sha256' in phase2_algos:
                        commands.append("esp authentication-algorithm sha2-256")
                    elif 'sha1' in phase2_algos:
                        commands.append("esp authentication-algorithm sha1")
                    elif 'md5' in phase2_algos:
                        commands.append("esp authentication-algorithm md5")
                else:
                    # 使用默认安全设置
                    commands.append("esp encryption-algorithm aes-256")
                    commands.append("esp authentication-algorithm sha2-256")
                
                # 设置IPSec SA生存周期
                lifetime = ipsec_settings.get('lifetime', {}).get('phase2', 3600)
                commands.append(f"sa duration-time-based {lifetime}")
                commands.append("quit")
            
            # 配置隧道参数
            if tunnel_settings:
                local_subnet = tunnel_settings.get('local_subnet')
                remote_subnet = tunnel_settings.get('remote_subnet')
                remote_gateway = tunnel_settings.get('remote_gateway')
                
                if local_subnet and remote_subnet and remote_gateway:
                    # 配置ACL规则
                    commands.append("acl 3000")
                    commands.append(f"rule 5 permit ip source {local_subnet} destination {remote_subnet}")
                    commands.append("quit")
                    
                    # 配置IKE对等体
                    commands.append("ike peer peer1")
                    commands.append(f"pre-shared-key {ipsec_settings.get('authentication', {}).get('psk', '')}")
                    commands.append(f"remote-address {remote_gateway}")
                    commands.append("ike-proposal 10")
                    
                    # 配置高级选项
                    advanced = policy_config.get('advanced', {})
                    
                    if advanced.get('nat_traversal', True):
                        commands.append("nat traversal")
                    
                    if advanced.get('dpd_enabled', True):
                        commands.append("dpd")
                    
                    commands.append("quit")
                    
                    # 配置IPsec策略
                    commands.append("ipsec policy policy1 10 isakmp")
                    commands.append("security acl 3000")
                    commands.append("ipsec proposal ipsec-prop1")
                    commands.append("ike-peer peer1")
                    
                    if advanced.get('perfect_forward_secrecy', True):
                        commands.append("pfs dh-group14")
                    
                    commands.append("quit")
            
            # 配置防火墙规则
            if firewall_settings:
                default_action = firewall_settings.get('default_action', 'deny')
                allowed_protocols = firewall_settings.get('allowed_protocols', [])
                
                # 创建安全区域规则
                commands.append("security-policy")
                
                # 允许IPSec相关协议
                for proto in allowed_protocols:
                    protocol = proto.get('protocol')
                    port = proto.get('port')
                    description = proto.get('description', '')
                    
                    if protocol == 'esp':
                        commands.append(f"rule name {description}")
                        commands.append("action permit")
                        commands.append("service protocol esp")
                        commands.append("quit")
                    elif protocol == 'udp' and port:
                        commands.append(f"rule name {description}")
                        commands.append("action permit")
                        commands.append(f"service protocol udp destination-port {port}")
                        commands.append("quit")
                
                # 应用到接口
                commands.append("interface GigabitEthernet 0/0/0")
                commands.append("ipsec policy policy1")
                commands.append("quit")
        
        # 保存配置
        commands.append("return")
        commands.append("save")
        commands.append("Y")
        
        return commands
    
    def _get_policy_status_commands(self, policy_id: str) -> List[str]:
        """获取策略状态的命令（华为设备）
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 命令列表
        """
        return [
            "display ipsec sa",
            "display ike sa"
        ]
    
    def _get_rollback_commands(self, policy_id: str) -> List[str]:
        """获取策略回滚的命令（华为设备）
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 命令列表
        """
        return [
            "system-view",
            "interface GigabitEthernet 0/0/0",
            "undo ipsec policy",
            "quit",
            "undo ipsec policy policy1",
            "undo ike peer peer1",
            "undo ipsec proposal ipsec-prop1",
            "undo acl 3000",
            "return",
            "save",
            "Y"
        ]
    
    def _parse_policy_status(self, result: str) -> Dict[str, Any]:
        """解析策略状态（华为设备）
        
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
        if "IPSec SA established" in result:
            status['status'] = 'active'
            status['details']['tunnels'] = []
            
            # 提取隧道信息 - 华为格式
            tunnel_matches = re.finditer(r'Tunnel id:\s+(\d+).*?Encapsulation mode:\s+(\w+).*?Local\s+address:\s+(\S+).*?Remote address:\s+(\S+)', 
                                        result, re.DOTALL)
            
            for match in tunnel_matches:
                tunnel = {
                    'tunnel_id': match.group(1),
                    'mode': match.group(2),
                    'local_ip': match.group(3),
                    'remote_ip': match.group(4)
                }
                status['details']['tunnels'].append(tunnel)
        
        # 检查IKE状态
        if "Established" in result:
            status['details']['ike_state'] = "Established"
        elif "Connecting" in result:
            status['details']['ike_state'] = "Connecting"
            if status['status'] == 'unknown':
                status['status'] = 'connecting'
        elif "Not Found" in result:
            status['details']['ike_state'] = "Not Found"
            if status['status'] == 'unknown':
                status['status'] = 'inactive'
        
        return status 