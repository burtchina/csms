#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
思科防火墙连接器实现
适用于思科ASA系列防火墙设备
"""

import re
import logging
from typing import Dict, Any, Tuple, List

from src.modules.policy.connectors.generic_connector import GenericFirewallConnector


class CiscoFirewallConnector(GenericFirewallConnector):
    """思科防火墙连接器，继承自通用连接器，针对思科ASA设备进行定制"""
    
    def __init__(self, timeout: int = 30, retry_count: int = 3, retry_interval: int = 5):
        """初始化连接器
        
        Args:
            timeout: 连接超时时间（秒）
            retry_count: 连接重试次数
            retry_interval: 重试间隔（秒）
        """
        super().__init__(timeout, retry_count, retry_interval)
    
    def _generate_firewall_commands(self, policy_config: Dict[str, Any]) -> List[str]:
        """根据策略配置生成思科防火墙命令
        
        Args:
            policy_config: 策略配置数据
            
        Returns:
            List[str]: 命令列表
        """
        commands = []
        
        # 进入配置模式
        commands.append("conf t")
        
        # 处理IPSec策略配置
        if policy_config.get('type') == 'ipsec':
            ipsec_settings = policy_config.get('ipsec_settings', {})
            firewall_settings = policy_config.get('firewall_settings', {})
            tunnel_settings = policy_config.get('tunnel_settings', {})
            
            # 配置ISAKMP策略
            if ipsec_settings:
                phase1_algos = ipsec_settings.get('encryption', {}).get('phase1', [])
                phase2_algos = ipsec_settings.get('encryption', {}).get('phase2', [])
                
                # ISAKMP策略配置
                commands.append("crypto isakmp policy 10")
                
                # 加密算法（默认AES-256）
                if phase1_algos:
                    if 'aes-256' in phase1_algos:
                        commands.append("encryption aes-256")
                    elif 'aes-128' in phase1_algos:
                        commands.append("encryption aes")
                    elif 'des' in phase1_algos:
                        commands.append("encryption des")
                else:
                    commands.append("encryption aes-256")
                
                # 哈希算法（默认SHA）
                if phase1_algos:
                    if 'sha256' in phase1_algos:
                        commands.append("hash sha")
                    elif 'md5' in phase1_algos:
                        commands.append("hash md5")
                else:
                    commands.append("hash sha")
                
                # 认证方式
                auth_method = ipsec_settings.get('authentication', {}).get('method', 'psk')
                if auth_method == 'psk':
                    commands.append("authentication pre-share")
                
                # DH组（默认group2）
                if phase1_algos:
                    if 'dh-group14' in phase1_algos:
                        commands.append("group 14")
                    elif 'dh-group5' in phase1_algos:
                        commands.append("group 5")
                    elif 'dh-group2' in phase1_algos:
                        commands.append("group 2")
                else:
                    commands.append("group 2")
                
                # 生存周期
                lifetime = ipsec_settings.get('lifetime', {}).get('phase1', 86400)
                commands.append(f"lifetime {lifetime}")
                commands.append("exit")
                
                # 设置预共享密钥
                psk = ipsec_settings.get('authentication', {}).get('psk', '')
                if psk and tunnel_settings.get('remote_gateway'):
                    commands.append(f"crypto isakmp key {psk} address {tunnel_settings.get('remote_gateway')}")
                
                # 配置IPSec变换集
                commands.append("crypto ipsec transform-set TS esp-aes-256 esp-sha-hmac")
                commands.append("mode tunnel")
                commands.append("exit")
            
            # 配置隧道和ACL
            if tunnel_settings:
                local_subnet = tunnel_settings.get('local_subnet')
                remote_subnet = tunnel_settings.get('remote_subnet')
                remote_gateway = tunnel_settings.get('remote_gateway')
                
                if local_subnet and remote_subnet:
                    # 创建ACL定义感兴趣流量
                    commands.append(f"access-list VPN-TRAFFIC extended permit ip {local_subnet} {remote_subnet}")
                
                # 创建加密映射
                if remote_gateway:
                    commands.append("crypto map CRYPTO-MAP 10 match address VPN-TRAFFIC")
                    commands.append("crypto map CRYPTO-MAP 10 set peer " + remote_gateway)
                    commands.append("crypto map CRYPTO-MAP 10 set transform-set TS")
                    
                    # 配置高级选项
                    advanced = policy_config.get('advanced', {})
                    
                    # 完美前向保密
                    if advanced.get('perfect_forward_secrecy', True):
                        commands.append("crypto map CRYPTO-MAP 10 set pfs group2")
                    
                    # IPSec SA生存周期
                    lifetime = ipsec_settings.get('lifetime', {}).get('phase2', 3600)
                    commands.append(f"crypto map CRYPTO-MAP 10 set security-association lifetime seconds {lifetime}")
            
            # 防火墙安全规则配置
            if firewall_settings:
                allowed_protocols = firewall_settings.get('allowed_protocols', [])
                
                # 允许IPSec相关协议通过
                for proto in allowed_protocols:
                    protocol = proto.get('protocol')
                    port = proto.get('port')
                    
                    if protocol == 'esp':
                        commands.append("access-list OUTSIDE-IN extended permit esp any any")
                    elif protocol == 'udp' and port:
                        commands.append(f"access-list OUTSIDE-IN extended permit udp any any eq {port}")
            
            # 应用加密映射到接口
            commands.append("interface GigabitEthernet0/0")
            commands.append("crypto map CRYPTO-MAP")
            commands.append("exit")
            
            # 启用ISAKMP
            commands.append("crypto isakmp enable outside")
        
        # 保存配置
        commands.append("end")
        commands.append("write memory")
        
        return commands
    
    def _get_policy_status_commands(self, policy_id: str) -> List[str]:
        """获取策略状态的命令（思科设备）
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 命令列表
        """
        return [
            "show crypto isakmp sa",
            "show crypto ipsec sa"
        ]
    
    def _get_rollback_commands(self, policy_id: str) -> List[str]:
        """获取策略回滚的命令（思科设备）
        
        Args:
            policy_id: 策略ID或标识
            
        Returns:
            List[str]: 命令列表
        """
        return [
            "conf t",
            "interface GigabitEthernet0/0",
            "no crypto map CRYPTO-MAP",
            "exit",
            "no crypto map CRYPTO-MAP 10",
            "no crypto isakmp policy 10",
            "no access-list VPN-TRAFFIC",
            "end",
            "write memory"
        ]
    
    def _parse_policy_status(self, result: str) -> Dict[str, Any]:
        """解析策略状态（思科设备）
        
        Args:
            result: 命令执行结果
            
        Returns:
            Dict[str, Any]: 策略状态信息
        """
        status = {
            'status': 'unknown',
            'details': {}
        }
        
        # 检查ISAKMP SA状态
        if "ACTIVE" in result or "MM_ACTIVE" in result or "QM_IDLE" in result:
            status['status'] = 'active'
            status['details']['isakmp_state'] = "Active"
            
            # 提取ISAKMP信息
            isakmp_matches = re.finditer(r'(\d+\.\d+\.\d+\.\d+).*?(\d+\.\d+\.\d+\.\d+).*?(MM_ACTIVE|ACTIVE)', result)
            
            if not 'peers' in status['details']:
                status['details']['peers'] = []
                
            for match in isakmp_matches:
                peer = {
                    'local_ip': match.group(1),
                    'remote_ip': match.group(2),
                    'state': match.group(3)
                }
                status['details']['peers'].append(peer)
        
        # 检查IPSec SA状态
        if "#pkts encaps:" in result:
            # 提取IPSec隧道统计信息
            if not 'tunnels' in status['details']:
                status['details']['tunnels'] = []
                
            tunnel_matches = re.finditer(r'local\s+ident\s+\((.*?)\).*?remote\s+ident\s+\((.*?)\).*?#pkts\s+encaps:\s+(\d+).*?#pkts\s+decrypt:\s+(\d+)', 
                                        result, re.DOTALL)
            
            for match in tunnel_matches:
                tunnel = {
                    'local_subnet': match.group(1),
                    'remote_subnet': match.group(2),
                    'pkts_encaps': match.group(3),
                    'pkts_decrypt': match.group(4)
                }
                status['details']['tunnels'].append(tunnel)
                
            if status['status'] == 'unknown' and len(status['details'].get('tunnels', [])) > 0:
                status['status'] = 'active'
        
        # 如果未检测到活跃状态，则标记为inactive
        if status['status'] == 'unknown' and "no SAs found" in result:
            status['status'] = 'inactive'
            status['details']['reason'] = "No Security Associations found"
        
        return status 