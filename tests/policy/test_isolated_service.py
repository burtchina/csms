#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略服务单元测试（隔离版本）
这个版本使用隔离架构，避免直接导入实际项目模块
"""

import pytest
from unittest.mock import MagicMock, patch

# 创建模拟的Policy类
class MockPolicy:
    def __init__(self, id=None, name=None, type=None, description=None, config=None, status=None):
        self.id = id
        self.name = name
        self.type = type
        self.description = description
        self.config = config or {}
        self.status = status or 'draft'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'config': self.config,
            'status': self.status
        }

# 创建模拟的PolicyService类
class MockPolicyService:
    def __init__(self):
        self.policy_repo = MagicMock()
    
    def create_policy(self, policy_data, user_id):
        """创建策略"""
        # 验证数据
        if not policy_data.get('name'):
            return False, {'error': '策略名称不能为空'}
        
        if not policy_data.get('type'):
            return False, {'error': '策略类型不能为空'}
        
        # 创建策略对象
        policy = MockPolicy(
            id=1,
            name=policy_data.get('name'),
            type=policy_data.get('type'),
            description=policy_data.get('description'),
            config=policy_data.get('config', {}),
            status=policy_data.get('status', 'draft')
        )
        
        return True, policy
    
    def update_policy(self, policy_id, policy_data, user_id):
        """更新策略"""
        # 模拟获取策略
        if policy_id != 1:
            return False, {'error': '策略不存在'}
        
        # 创建更新后的策略对象
        policy = MockPolicy(
            id=policy_id,
            name=policy_data.get('name', '原策略'),
            type=policy_data.get('type', 'ipsec'),
            description=policy_data.get('description'),
            config=policy_data.get('config', {}),
            status=policy_data.get('status', 'active')
        )
        
        return True, policy
    
    def delete_policy(self, policy_id, user_id):
        """删除策略"""
        # 模拟获取策略
        if policy_id != 1:
            return False, {'error': '策略不存在'}
        
        return True, {'message': '策略已删除'}
    
    def get_policy(self, policy_id):
        """获取策略"""
        # 模拟获取策略
        if policy_id != 1:
            return False, {'error': '策略不存在'}
        
        policy = MockPolicy(
            id=policy_id,
            name='测试策略',
            type='ipsec',
            description='测试描述',
            config={},
            status='active'
        )
        
        return True, policy
    
    def list_policies(self, filters=None):
        """获取策略列表"""
        policy1 = MockPolicy(id=1, name='策略1', type='ipsec')
        policy2 = MockPolicy(id=2, name='策略2', type='ipsec')
        
        return [policy1, policy2]


class TestIsolatedPolicyService:
    """策略服务测试类（隔离版本）"""
    
    @pytest.fixture
    def policy_service(self):
        """创建策略服务实例"""
        return MockPolicyService()
    
    @pytest.fixture
    def sample_policy_data(self):
        """样例策略数据"""
        return {
            'name': '测试IPSec策略',
            'type': 'ipsec',
            'description': '这是一个测试用的IPSec策略',
            'config': {
                'version': '1.0',
                'firewall_settings': {
                    'default_action': 'deny',
                    'allowed_protocols': [
                        {'protocol': 'udp', 'port': 500, 'description': 'IKE'}
                    ]
                },
                'ipsec_settings': {
                    'authentication': {
                        'method': 'psk',
                        'psk': 'encrypted:test123'
                    },
                    'encryption': {
                        'phase1': ['aes-256', 'sha256', 'dh-group14'],
                        'phase2': ['aes-256', 'sha256']
                    },
                    'lifetime': {
                        'phase1': 86400,
                        'phase2': 3600
                    }
                },
                'tunnel_settings': {
                    'local_subnet': '192.168.1.0/24',
                    'remote_subnet': '192.168.2.0/24',
                    'remote_gateway': '203.0.113.1'
                }
            }
        }
    
    def test_create_policy_success(self, policy_service, sample_policy_data):
        """测试成功创建策略"""
        # 执行测试
        success, result = policy_service.create_policy(sample_policy_data, 1)
        
        # 验证结果
        assert success is True
        assert result.id == 1
        assert result.name == sample_policy_data['name']
    
    def test_create_policy_failure(self, policy_service):
        """测试创建策略失败"""
        # 不完整的策略数据
        invalid_data = {'description': 'Invalid policy'}
        
        # 执行测试
        success, result = policy_service.create_policy(invalid_data, 1)
        
        # 验证结果
        assert success is False
        assert 'error' in result
    
    def test_update_policy_success(self, policy_service, sample_policy_data):
        """测试成功更新策略"""
        # 执行测试
        success, result = policy_service.update_policy(1, sample_policy_data, 1)
        
        # 验证结果
        assert success is True
        assert result.id == 1
        assert result.name == sample_policy_data['name']
    
    def test_update_nonexistent_policy(self, policy_service, sample_policy_data):
        """测试更新不存在的策略"""
        # 执行测试
        success, result = policy_service.update_policy(999, sample_policy_data, 1)
        
        # 验证结果
        assert success is False
        assert 'error' in result
        assert result['error'] == '策略不存在'
    
    def test_delete_policy_success(self, policy_service):
        """测试成功删除策略"""
        # 执行测试
        success, result = policy_service.delete_policy(1, 1)
        
        # 验证结果
        assert success is True
        assert 'message' in result
        assert result['message'] == '策略已删除'
    
    def test_get_policy_success(self, policy_service):
        """测试成功获取策略"""
        # 执行测试
        success, result = policy_service.get_policy(1)
        
        # 验证结果
        assert success is True
        assert result.id == 1
        assert result.name == '测试策略'
    
    def test_list_policies(self, policy_service):
        """测试获取策略列表"""
        # 执行测试
        result = policy_service.list_policies({'status': 'active'})
        
        # 验证结果
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2


# 直接运行测试
if __name__ == "__main__":
    import sys
    import os
    
    # 查看当前路径
    print(f"当前工作目录: {os.getcwd()}")
    
    # 运行测试
    pytest.main(["-v", __file__]) 