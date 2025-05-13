#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化IPSec与防火墙联动策略的系统预设模板
包括三种模式：未限制、仅允许IPSec流量、仅允许IPSec流量和合作学校IP
"""

import sys
import os
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 保持与策略模型一致的导入
from src.core.db import db
# 不再需要current_app，因为在app.py中使用app_context
# from flask import current_app
from src.modules.policy.models.policy_template import PolicyTemplate
# 修复导入路径
from src.modules.auth.models import User

def init_policy_templates():
    """初始化系统预设IPSec与防火墙联动策略模板"""
    # 添加日志
    logging.info("开始初始化系统预设IPSec与防火墙联动策略模板")
    
    # 检查是否已存在系统预设模板
    existing_templates = PolicyTemplate.query.filter_by(is_system=True, type='ipsec_firewall').all()
    if existing_templates:
        logging.info(f"已存在 {len(existing_templates)} 个系统预设IPSec与防火墙联动策略模板，跳过初始化。")
        return
    
    # 获取管理员用户ID
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        logging.warning("错误：找不到管理员用户，无法创建系统预设模板。")
        return
    
    admin_id = admin_user.id
    logging.info(f"找到管理员用户ID: {admin_id}，继续初始化模板")
    
    # 定义模板列表
    templates = [
        {
            "name": "IPSec与防火墙联动 - 未限制",
            "type": "ipsec_firewall",
            "description": "允许所有流量通过的IPSec与防火墙联动策略，适用于不需要严格网络控制的场景。",
            "is_system": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow(),
            "config": {
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "allow",
                    "allowed_protocols": []
                },
                "ipsec_settings": {
                    "authentication": {
                        "method": "psk",
                        "psk": ""
                    },
                    "encryption": {
                        "phase1": ["aes-256", "sha256", "dh-group14"],
                        "phase2": ["aes-256", "sha256"]
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
                "source_restrictions": {
                    "allowed_ips": [],
                    "allowed_domains": []
                },
                "advanced": {
                    "dpd_enabled": True,
                    "dpd_delay": 30,
                    "dpd_timeout": 120,
                    "nat_traversal": True,
                    "perfect_forward_secrecy": True
                }
            }
        },
        {
            "name": "IPSec与防火墙联动 - 仅允许IPSec流量",
            "type": "ipsec_firewall",
            "description": "只允许IPSec相关协议通过的联动策略，拒绝其他所有流量，适用于安全要求较高的VPN连接。",
            "is_system": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow(),
            "config": {
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "deny",
                    "allowed_protocols": [
                        {
                            "protocol": "udp",
                            "port": 500,
                            "description": "IKE"
                        },
                        {
                            "protocol": "udp",
                            "port": 4500,
                            "description": "NAT-T"
                        },
                        {
                            "protocol": "esp",
                            "description": "ESP Protocol"
                        }
                    ]
                },
                "ipsec_settings": {
                    "authentication": {
                        "method": "psk",
                        "psk": ""
                    },
                    "encryption": {
                        "phase1": ["aes-256", "sha256", "dh-group14"],
                        "phase2": ["aes-256", "sha256"]
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
                "source_restrictions": {
                    "allowed_ips": [],
                    "allowed_domains": []
                },
                "advanced": {
                    "dpd_enabled": True,
                    "dpd_delay": 30,
                    "dpd_timeout": 120,
                    "nat_traversal": True,
                    "perfect_forward_secrecy": True
                }
            }
        },
        {
            "name": "IPSec与防火墙联动 - 仅允许IPSec流量和合作学校IP",
            "type": "ipsec_firewall",
            "description": "只允许IPSec相关协议和特定合作学校IP地址通过的联动策略，适用于校际合作网络。",
            "is_system": True,
            "created_by": admin_id,
            "created_at": datetime.utcnow(),
            "config": {
                "version": "1.0",
                "firewall_settings": {
                    "default_action": "deny",
                    "allowed_protocols": [
                        {
                            "protocol": "udp",
                            "port": 500,
                            "description": "IKE"
                        },
                        {
                            "protocol": "udp",
                            "port": 4500,
                            "description": "NAT-T"
                        },
                        {
                            "protocol": "esp",
                            "description": "ESP Protocol"
                        }
                    ]
                },
                "ipsec_settings": {
                    "authentication": {
                        "method": "psk",
                        "psk": ""
                    },
                    "encryption": {
                        "phase1": ["aes-256", "sha256", "dh-group14"],
                        "phase2": ["aes-256", "sha256"]
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
                "source_restrictions": {
                    "allowed_ips": ["203.0.113.0/24", "198.51.100.0/24"],
                    "allowed_domains": ["partner-university.edu"]
                },
                "advanced": {
                    "dpd_enabled": True,
                    "dpd_delay": 30,
                    "dpd_timeout": 120,
                    "nat_traversal": True,
                    "perfect_forward_secrecy": True
                }
            }
        }
    ]
    
    # 创建模板
    try:
        logging.info(f"开始创建 {len(templates)} 个系统预设模板")
        for template_data in templates:
            template = PolicyTemplate(**template_data)
            db.session.add(template)
        
        db.session.commit()
        logging.info(f"成功创建 {len(templates)} 个系统预设IPSec与防火墙联动策略模板")
    except Exception as e:
        db.session.rollback()
        logging.error(f"创建系统预设模板失败: {str(e)}")
        raise  # 重新抛出异常，让调用者知道出了问题

if __name__ == "__main__":
    # 直接运行此脚本时，需要创建应用上下文
    from src.app import create_app
    app = create_app()
    # 设置日志
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    with app.app_context():
        init_policy_templates() 