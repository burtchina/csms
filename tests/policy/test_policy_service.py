#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略服务单元测试
"""

import os
import sys
import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 添加Mock解决flask_jwt_extended依赖问题
sys.modules['flask_jwt_extended'] = MagicMock()
sys.modules['flask'] = MagicMock()

from src.modules.policy.services.policy_service import PolicyService
from src.modules.policy.models.policy import Policy


class TestPolicyService:
    """策略服务测试类"""
    
    @pytest.fixture
    def policy_service(self):
        """创建策略服务实例"""
        return PolicyService()
    
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
        with patch('src.modules.policy.validators.policy_validator.PolicyValidator.validate_policy', return_value=(True, None)):
            with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.create') as mock_create:
                # 设置模拟返回值
                mock_policy = MagicMock(spec=Policy)
                mock_policy.id = 1
                mock_policy.name = sample_policy_data['name']
                mock_create.return_value = mock_policy
                
                # 模拟审计日志
                with patch('src.modules.policy.services.policy_service.PolicyService._create_audit_log') as mock_audit:
                    # 执行测试
                    success, result = policy_service.create_policy(sample_policy_data, 1)
                    
                    # 验证结果
                    assert success is True
                    assert result.id == 1
                    assert result.name == sample_policy_data['name']
                    
                    # 验证调用
                    mock_create.assert_called_once()
                    mock_audit.assert_called_once()
    
    def test_create_policy_validation_failed(self, policy_service, sample_policy_data):
        """测试创建策略验证失败"""
        with patch('src.modules.policy.validators.policy_validator.PolicyValidator.validate_policy', 
                   return_value=(False, '策略配置无效')):
            # 执行测试
            success, result = policy_service.create_policy(sample_policy_data, 1)
            
            # 验证结果
            assert success is False
            assert 'error' in result
            assert result['error'] == '策略配置无效'
    
    def test_update_policy_success(self, policy_service, sample_policy_data):
        """测试成功更新策略"""
        with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.get_by_id') as mock_get:
            # 设置模拟返回值
            mock_policy = MagicMock(spec=Policy)
            mock_policy.id = 1
            mock_policy.name = '原策略名称'
            mock_policy.status = 'active'
            mock_policy.type = 'ipsec'
            mock_get.return_value = mock_policy
            
            with patch('src.modules.policy.validators.policy_validator.PolicyValidator.validate_policy', 
                      return_value=(True, None)):
                with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.update') as mock_update:
                    # 设置更新后的策略
                    updated_policy = MagicMock(spec=Policy)
                    updated_policy.id = 1
                    updated_policy.name = sample_policy_data['name']
                    mock_update.return_value = updated_policy
                    
                    # 模拟审计日志
                    with patch('src.modules.policy.services.policy_service.PolicyService._create_audit_log') as mock_audit:
                        # 执行测试
                        success, result = policy_service.update_policy(1, sample_policy_data, 1)
                        
                        # 验证结果
                        assert success is True
                        assert result.id == 1
                        assert result.name == sample_policy_data['name']
                        
                        # 验证调用
                        mock_update.assert_called_once()
                        mock_audit.assert_called_once()
    
    def test_update_nonexistent_policy(self, policy_service, sample_policy_data):
        """测试更新不存在的策略"""
        with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.get_by_id', 
                  return_value=None):
            # 执行测试
            success, result = policy_service.update_policy(999, sample_policy_data, 1)
            
            # 验证结果
            assert success is False
            assert 'error' in result
            assert result['error'] == '策略不存在'
    
    def test_delete_policy_success(self, policy_service):
        """测试成功删除策略"""
        with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.get_by_id') as mock_get:
            # 设置模拟返回值
            mock_policy = MagicMock(spec=Policy)
            mock_policy.id = 1
            mock_policy.name = '测试策略'
            mock_policy.status = 'active'
            mock_get.return_value = mock_policy
            
            with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.delete', 
                      return_value=True) as mock_delete:
                # 模拟审计日志
                with patch('src.modules.policy.services.policy_service.PolicyService._create_audit_log') as mock_audit:
                    # 执行测试
                    success, result = policy_service.delete_policy(1, 1)
                    
                    # 验证结果
                    assert success is True
                    assert 'message' in result
                    assert result['message'] == '策略已删除'
                    
                    # 验证调用
                    mock_delete.assert_called_once_with(1)
                    mock_audit.assert_called_once()
    
    def test_get_policy_success(self, policy_service):
        """测试成功获取策略"""
        with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.get_by_id') as mock_get:
            # 设置模拟返回值
            mock_policy = MagicMock(spec=Policy)
            mock_policy.id = 1
            mock_policy.name = '测试策略'
            mock_get.return_value = mock_policy
            
            # 执行测试
            success, result = policy_service.get_policy(1)
            
            # 验证结果
            assert success is True
            assert result.id == 1
            assert result.name == '测试策略'
    
    def test_list_policies(self, policy_service):
        """测试获取策略列表"""
        with patch('src.modules.policy.repositories.policy_repository.PolicyRepository.get_all') as mock_get_all:
            # 设置模拟返回值
            mock_policy1 = MagicMock(spec=Policy)
            mock_policy1.id = 1
            mock_policy1.name = '测试策略1'
            
            mock_policy2 = MagicMock(spec=Policy)
            mock_policy2.id = 2
            mock_policy2.name = '测试策略2'
            
            mock_get_all.return_value = [mock_policy1, mock_policy2]
            
            # 执行测试
            result = policy_service.list_policies({'status': 'active'})
            
            # 验证结果
            assert len(result) == 2
            assert result[0].id == 1
            assert result[1].id == 2
            
            # 验证调用参数
            mock_get_all.assert_called_once_with({'status': 'active'}) 