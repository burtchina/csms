#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略验证器
用于验证策略数据的有效性
"""

from jsonschema import validate, ValidationError

class PolicyValidator:
    """策略验证器"""
    
    # IPSec策略JSON Schema
    IPSEC_POLICY_SCHEMA = {
        "type": "object",
        "required": ["version", "firewall_settings", "ipsec_settings"],
        "properties": {
            "version": {"type": "string"},
            "firewall_settings": {
                "type": "object",
                "required": ["default_action", "allowed_protocols"],
                "properties": {
                    "default_action": {"type": "string", "enum": ["deny", "allow"]},
                    "allowed_protocols": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["protocol"],
                            "properties": {
                                "protocol": {"type": "string"},
                                "port": {"type": "integer"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "ipsec_settings": {
                "type": "object",
                "required": ["authentication", "encryption", "lifetime"],
                "properties": {
                    "authentication": {
                        "type": "object",
                        "required": ["method"],
                        "properties": {
                            "method": {"type": "string", "enum": ["psk", "cert"]},
                            "psk": {"type": "string"}
                        }
                    },
                    "encryption": {
                        "type": "object",
                        "required": ["phase1", "phase2"],
                        "properties": {
                            "phase1": {"type": "array", "items": {"type": "string"}},
                            "phase2": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "lifetime": {
                        "type": "object",
                        "required": ["phase1", "phase2"],
                        "properties": {
                            "phase1": {"type": "integer", "minimum": 300},
                            "phase2": {"type": "integer", "minimum": 300}
                        }
                    }
                }
            },
            "tunnel_settings": {
                "type": "object",
                "properties": {
                    "local_subnet": {"type": "string"},
                    "remote_subnet": {"type": "string"},
                    "remote_gateway": {"type": "string"}
                }
            },
            "source_restrictions": {
                "type": "object",
                "properties": {
                    "allowed_ips": {"type": "array", "items": {"type": "string"}},
                    "allowed_domains": {"type": "array", "items": {"type": "string"}}
                }
            },
            "advanced": {
                "type": "object",
                "properties": {
                    "dpd_enabled": {"type": "boolean"},
                    "dpd_delay": {"type": "integer"},
                    "dpd_timeout": {"type": "integer"},
                    "nat_traversal": {"type": "boolean"},
                    "perfect_forward_secrecy": {"type": "boolean"}
                }
            }
        }
    }
    
    # 传统IPSec策略JSON Schema，需要tunnel_settings
    IPSEC_TUNNEL_POLICY_SCHEMA = {
        "type": "object",
        "required": ["version", "firewall_settings", "ipsec_settings", "tunnel_settings"],
        "properties": {
            "version": {"type": "string"},
            "firewall_settings": {
                "type": "object",
                "required": ["default_action", "allowed_protocols"],
                "properties": {
                    "default_action": {"type": "string", "enum": ["deny", "allow"]},
                    "allowed_protocols": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["protocol"],
                            "properties": {
                                "protocol": {"type": "string"},
                                "port": {"type": "integer"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "ipsec_settings": {
                "type": "object",
                "required": ["authentication", "encryption", "lifetime"],
                "properties": {
                    "authentication": {
                        "type": "object",
                        "required": ["method"],
                        "properties": {
                            "method": {"type": "string", "enum": ["psk", "cert"]},
                            "psk": {"type": "string"}
                        }
                    },
                    "encryption": {
                        "type": "object",
                        "required": ["phase1", "phase2"],
                        "properties": {
                            "phase1": {"type": "array", "items": {"type": "string"}},
                            "phase2": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "lifetime": {
                        "type": "object",
                        "required": ["phase1", "phase2"],
                        "properties": {
                            "phase1": {"type": "integer", "minimum": 300},
                            "phase2": {"type": "integer", "minimum": 300}
                        }
                    }
                }
            },
            "tunnel_settings": {
                "type": "object",
                "required": ["local_subnet", "remote_subnet", "remote_gateway"],
                "properties": {
                    "local_subnet": {"type": "string"},
                    "remote_subnet": {"type": "string"},
                    "remote_gateway": {"type": "string"}
                }
            },
            "source_restrictions": {
                "type": "object",
                "properties": {
                    "allowed_ips": {"type": "array", "items": {"type": "string"}},
                    "allowed_domains": {"type": "array", "items": {"type": "string"}}
                }
            },
            "advanced": {
                "type": "object",
                "properties": {
                    "dpd_enabled": {"type": "boolean"},
                    "dpd_delay": {"type": "integer"},
                    "dpd_timeout": {"type": "integer"},
                    "nat_traversal": {"type": "boolean"},
                    "perfect_forward_secrecy": {"type": "boolean"}
                }
            }
        }
    }
    
    @classmethod
    def validate_policy(cls, policy_data):
        """验证策略数据
        
        Args:
            policy_data (dict): 要验证的策略数据
            
        Returns:
            tuple: (is_valid, errors)
        """
        if not isinstance(policy_data, dict):
            return False, "策略数据必须是字典类型"
        
        if 'type' not in policy_data:
            return False, "策略必须指定类型"
        
        if 'name' not in policy_data or not policy_data['name']:
            return False, "策略必须有名称"
        
        if 'config' not in policy_data or not isinstance(policy_data['config'], dict):
            return False, "策略必须包含配置信息"
        
        # 根据策略类型选择验证方式
        policy_type = policy_data['type']
        config = policy_data['config']
        
        if policy_type == 'ipsec':
            # 传统IPSec策略，需要tunnel_settings
            return cls.validate_ipsec_tunnel_policy(config)
        elif policy_type == 'allow_all' or policy_type == 'ipsec_only' or policy_type == 'ipsec_specific_ip':
            # 新的IPSec联动策略类型，不严格要求tunnel_settings
            return cls.validate_ipsec_policy(config)
        else:
            return False, f"不支持的策略类型: {policy_type}"
    
    @classmethod
    def validate_ipsec_policy(cls, config):
        """验证IPSec策略配置（不严格要求tunnel_settings）
        
        Args:
            config (dict): IPSec策略配置
            
        Returns:
            tuple: (is_valid, errors)
        """
        try:
            validate(instance=config, schema=cls.IPSEC_POLICY_SCHEMA)
            
            # 如果存在tunnel_settings，则验证其格式
            if 'tunnel_settings' in config:
                tunnel = config['tunnel_settings']
                if tunnel.get('local_subnet') and not cls._is_valid_subnet(tunnel.get('local_subnet')):
                    return False, "本地子网格式无效"
                if tunnel.get('remote_subnet') and not cls._is_valid_subnet(tunnel.get('remote_subnet')):
                    return False, "远程子网格式无效"
                if tunnel.get('remote_gateway') and not cls._is_valid_ip(tunnel.get('remote_gateway')):
                    return False, "远程网关IP格式无效"
            
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @classmethod
    def validate_ipsec_tunnel_policy(cls, config):
        """验证需要tunnel_settings的IPSec策略配置
        
        Args:
            config (dict): IPSec策略配置
            
        Returns:
            tuple: (is_valid, errors)
        """
        try:
            validate(instance=config, schema=cls.IPSEC_TUNNEL_POLICY_SCHEMA)
            
            # 验证tunnel_settings（必需项）
            if 'tunnel_settings' in config:
                tunnel = config['tunnel_settings']
                if not cls._is_valid_subnet(tunnel.get('local_subnet', '')):
                    return False, "本地子网格式无效"
                if not cls._is_valid_subnet(tunnel.get('remote_subnet', '')):
                    return False, "远程子网格式无效"
                if not cls._is_valid_ip(tunnel.get('remote_gateway', '')):
                    return False, "远程网关IP格式无效"
            
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @staticmethod
    def _is_valid_ip(ip):
        """验证IP地址是否有效"""
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # 验证每个部分的范围
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        
        return True
    
    @staticmethod
    def _is_valid_subnet(subnet):
        """验证子网是否有效"""
        if not subnet:
            return False
            
        # 简单格式验证: IP/MASK
        import re
        pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(pattern, subnet):
            return False
        
        # 验证IP部分
        ip = subnet.split('/')[0]
        if not PolicyValidator._is_valid_ip(ip):
            return False
        
        # 验证掩码部分
        mask = int(subnet.split('/')[1])
        if mask < 0 or mask > 32:
            return False
        
        return True 