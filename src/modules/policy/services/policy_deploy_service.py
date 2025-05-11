#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略下发服务类
提供策略下发和同步相关的业务逻辑
"""

import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from src.core.db import db
from src.models.device import Device
from src.modules.policy.models.policy import Policy
from src.modules.policy.models.policy_deployment import PolicyDeployment
from src.modules.policy.repositories.policy_repository import PolicyRepository, PolicyDeploymentRepository, PolicyAuditLogRepository
from src.modules.policy.connectors.connector_factory import ConnectorFactory
from src.modules.policy.connectors.firewall_connector import FirewallConnector, FirewallConnectionError, FirewallDeployError


class PolicyDeployService:
    """策略下发服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.policy_repo = PolicyRepository(db.session)
        self.deployment_repo = PolicyDeploymentRepository(db.session)
        self.audit_repo = PolicyAuditLogRepository(db.session)
    
    def deploy_policy(self, policy_id: int, device_id: int, user_id: int, options: Dict[str, bool] = None) -> Tuple[bool, Any]:
        """部署策略到设备
        
        Args:
            policy_id: 策略ID
            device_id: 设备ID
            user_id: 操作用户ID
            options: 部署选项，包含verify_before_deploy, verify_after_deploy, enable_rollback, log_deployment等
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 设置默认选项
        if options is None:
            options = {
                'verify_before_deploy': True,
                'verify_after_deploy': True,
                'enable_rollback': True,
                'log_deployment': True
            }
        
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = Device.query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        # 检查策略状态
        if policy.status != 'active':
            return False, {'error': f'只能下发状态为active的策略，当前状态: {policy.status}'}
        
        # 策略部署前验证
        if options.get('verify_before_deploy', True):
            verify_success, verify_result = self.verify_policy(policy_id, device_id)
            if not verify_success:
                return False, {'error': f'策略部署前验证失败: {verify_result}'}
        
        # 创建部署记录
        deployment_data = {
            'policy_id': policy_id,
            'device_id': device_id,
            'status': 'pending',
            'deployed_at': datetime.utcnow(),
            'deployed_by': user_id,
            'config_snapshot': policy.config,
            'result': '策略下发中...'
        }
        
        try:
            # 保存部署记录
            deployment = self.deployment_repo.create(deployment_data)
            
            # 创建审计日志
            if options.get('log_deployment', True):
                self._create_audit_log(
                    policy_id=policy_id,
                    user_id=user_id,
                    action='deploy',
                    details=f'部署策略 {policy.name} 到设备 {device.name}'
                )
            
            # 连接设备并部署策略
            success, result = self._deploy_to_device(policy, device, deployment.id)
            
            # 部署后验证
            if success and options.get('verify_after_deploy', True):
                verify_after_success, _ = self.verify_policy(policy_id, device_id)
                if not verify_after_success:
                    success = False
                    result = '部署成功但部署后验证失败'
                    # 如果启用了自动回滚，进行回滚
                    if options.get('enable_rollback', True):
                        self._rollback_on_device(policy, device)
                        result += '，已自动回滚'
            
            # 更新部署状态
            status = 'success' if success else 'failed'
            self.deployment_repo.update(deployment.id, {
                'status': status,
                'result': result
            })
            
            if success:
                return True, {'message': f'策略部署成功: {result}', 'deployment_id': deployment.id}
            else:
                return False, {'error': f'策略部署失败: {result}', 'deployment_id': deployment.id}
                
        except Exception as e:
            logging.error(f"部署策略时发生错误: {str(e)}")
            
            # 如果已创建部署记录，更新状态为失败
            if 'deployment' in locals():
                self.deployment_repo.update(deployment.id, {
                    'status': 'failed',
                    'result': f'部署异常: {str(e)}'
                })
            
            # 如果启用了自动回滚，尝试回滚
            if options.get('enable_rollback', True) and 'policy' in locals() and 'device' in locals():
                try:
                    self._rollback_on_device(policy, device)
                except Exception as rollback_error:
                    logging.error(f"回滚策略时发生错误: {str(rollback_error)}")
            
            db.session.rollback()
            return False, {'error': str(e)}
    
    def get_policy_status(self, policy_id: int, device_id: int) -> Tuple[bool, Any]:
        """获取策略在设备上的部署状态
        
        Args:
            policy_id: 策略ID
            device_id: 设备ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 获取最新部署记录
        deployment = self.deployment_repo.get_latest_deployment(policy_id, device_id)
        if not deployment:
            return False, {'error': '未找到部署记录'}
        
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = Device.query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 获取设备上的策略状态
            device_status = self._get_device_policy_status(policy, device)
            
            # 更新部署记录的状态信息
            if device_status:
                self.deployment_repo.update(deployment.id, {
                    'result': json.dumps(device_status)
                })
            
            # 返回当前状态
            deployment_info = deployment.to_dict()
            
            # 添加实时设备状态
            deployment_info['device_status'] = device_status
            
            return True, deployment_info
            
        except Exception as e:
            logging.error(f"获取策略状态时发生错误: {str(e)}")
            return False, {'error': str(e), 'deployment_data': deployment.to_dict()}
    
    def sync_policy_status(self, policy_id: int = None, device_id: int = None) -> Dict[str, Any]:
        """同步策略状态（可由定时任务调用）
        
        Args:
            policy_id: 策略ID（可选，如果提供则只同步指定策略）
            device_id: 设备ID（可选，如果提供则只同步指定设备上的策略）
            
        Returns:
            Dict[str, Any]: 同步结果统计
        """
        # 获取需要同步的部署记录
        filters = {
            'status': 'success'  # 只同步成功部署的策略
        }
        
        if policy_id:
            filters['policy_id'] = policy_id
            
        if device_id:
            filters['device_id'] = device_id
        
        deployments = self.deployment_repo.get_all(filters)
        
        result = {
            'total': len(deployments),
            'success': 0,
            'failed': 0,
            'not_found': 0,
            'details': []
        }
        
        for deployment in deployments:
            try:
                policy = self.policy_repo.get_by_id(deployment.policy_id)
                device = Device.query.get(deployment.device_id)
                
                if not policy or not device:
                    result['not_found'] += 1
                    continue
                
                # 获取设备上的策略状态
                device_status = self._get_device_policy_status(policy, device)
                
                if device_status:
                    # 更新部署记录
                    self.deployment_repo.update(deployment.id, {
                        'result': json.dumps(device_status)
                    })
                    
                    result['success'] += 1
                    result['details'].append({
                        'policy_id': policy.id,
                        'policy_name': policy.name,
                        'device_id': device.id,
                        'device_name': device.name,
                        'status': device_status.get('status', 'unknown')
                    })
                else:
                    result['failed'] += 1
            
            except Exception as e:
                logging.error(f"同步策略状态时发生错误: 策略ID={deployment.policy_id}, 设备ID={deployment.device_id}, 错误: {str(e)}")
                result['failed'] += 1
        
        return result
    
    def rollback_policy(self, policy_id: int, device_id: int, user_id: int) -> Tuple[bool, Any]:
        """回滚策略
        
        Args:
            policy_id: 策略ID
            device_id: 设备ID
            user_id: 操作用户ID
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果/错误信息)
        """
        # 获取最新部署记录
        deployment = self.deployment_repo.get_latest_deployment(policy_id, device_id)
        if not deployment:
            return False, {'error': '未找到部署记录'}
        
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = Device.query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 创建新的部署记录用于回滚操作
            rollback_data = {
                'policy_id': policy_id,
                'device_id': device_id,
                'status': 'pending',
                'deployed_at': datetime.utcnow(),
                'deployed_by': user_id,
                'config_snapshot': deployment.config_snapshot,
                'result': '策略回滚中...'
            }
            
            # 保存回滚记录
            rollback_deployment = self.deployment_repo.create(rollback_data)
            
            # 创建审计日志
            self._create_audit_log(
                policy_id=policy_id,
                user_id=user_id,
                action='rollback',
                details=f'回滚策略 {policy.name} 在设备 {device.name} 上的部署'
            )
            
            # 连接设备并执行回滚
            success, result = self._rollback_on_device(policy, device)
            
            # 更新部署状态
            status = 'success' if success else 'failed'
            self.deployment_repo.update(rollback_deployment.id, {
                'status': status,
                'result': result
            })
            
            if success:
                return True, {'message': f'策略回滚成功: {result}', 'deployment_id': rollback_deployment.id}
            else:
                return False, {'error': f'策略回滚失败: {result}', 'deployment_id': rollback_deployment.id}
                
        except Exception as e:
            logging.error(f"回滚策略时发生错误: {str(e)}")
            
            # 如果已创建回滚记录，更新状态为失败
            if 'rollback_deployment' in locals():
                self.deployment_repo.update(rollback_deployment.id, {
                    'status': 'failed',
                    'result': f'回滚异常: {str(e)}'
                })
            
            db.session.rollback()
            return False, {'error': str(e)}
    
    def verify_policy(self, policy_id: int, device_id: int) -> Tuple[bool, Any]:
        """验证策略配置的有效性
        
        Args:
            policy_id: 策略ID
            device_id: 设备ID
            
        Returns:
            Tuple[bool, Any]: (是否成功，结果/错误信息)
        """
        # 获取策略和设备
        policy = self.policy_repo.get_by_id(policy_id)
        if not policy:
            return False, {'error': '策略不存在'}
        
        device = Device.query.get(device_id)
        if not device:
            return False, {'error': '设备不存在'}
        
        try:
            # 创建连接器
            connector = ConnectorFactory.create_and_connect(device)
            if not connector:
                return False, {'error': f'无法连接到设备 {device.name}'}
            
            try:
                # 验证策略
                is_valid, message = connector.verify_policy(policy.config)
                
                # 创建审计日志
                self._create_audit_log(
                    policy_id=policy_id,
                    user_id=1,  # 系统操作，使用ID 1
                    action='verify',
                    details=f'验证策略 {policy.name} 在设备 {device.name} 上的有效性: {message}'
                )
                
                return is_valid, {'message': message}
            finally:
                # 断开连接
                connector.disconnect()
        except Exception as e:
            logging.error(f"验证策略时发生错误: {str(e)}")
            return False, {'error': str(e)}
    
    def _deploy_to_device(self, policy: Policy, device: Device, deployment_id: int) -> Tuple[bool, str]:
        """将策略部署到设备
        
        Args:
            policy: 策略对象
            device: 设备对象
            deployment_id: 部署记录ID
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        try:
            # 连接设备
            connector = ConnectorFactory.create_and_connect(device)
            if not connector:
                return False, "无法连接到设备"
            
            try:
                # 部署策略
                success, message = connector.deploy_policy(policy.config)
                return success, message
            finally:
                # 断开连接
                connector.disconnect()
                
        except FirewallConnectionError as e:
            return False, f"连接设备失败: {str(e)}"
        except FirewallDeployError as e:
            return False, f"部署策略失败: {str(e)}"
        except Exception as e:
            return False, f"部署过程中发生错误: {str(e)}"
    
    def _get_device_policy_status(self, policy: Policy, device: Device) -> Optional[Dict[str, Any]]:
        """获取设备上的策略状态
        
        Args:
            policy: 策略对象
            device: 设备对象
            
        Returns:
            Optional[Dict[str, Any]]: 策略状态信息
        """
        try:
            # 连接设备
            connector = ConnectorFactory.create_and_connect(device)
            if not connector:
                logging.error(f"无法连接到设备 {device.name}")
                return {
                    'status': 'unknown',
                    'error': f'无法连接到设备 {device.name}',
                    'check_time': datetime.utcnow().isoformat()
                }
            
            try:
                # 获取策略状态
                status = connector.get_policy_status(str(policy.id))
                
                # 确保状态包含检查时间
                if 'check_time' not in status:
                    status['check_time'] = datetime.utcnow().isoformat()
                
                # 添加额外信息以便于追踪
                status['policy_id'] = policy.id
                status['policy_name'] = policy.name
                status['device_id'] = device.id
                status['device_name'] = device.name
                
                return status
            finally:
                # 断开连接
                connector.disconnect()
                
        except Exception as e:
            logging.error(f"获取策略状态时发生错误: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'check_time': datetime.utcnow().isoformat()
            }
    
    def _rollback_on_device(self, policy: Policy, device: Device) -> Tuple[bool, str]:
        """在设备上回滚策略
        
        Args:
            policy: 策略对象
            device: 设备对象
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        try:
            # 连接设备
            connector = ConnectorFactory.create_and_connect(device)
            if not connector:
                return False, "无法连接到设备"
            
            try:
                # 回滚策略
                success, message = connector.rollback_policy(str(policy.id))
                return success, message
            finally:
                # 断开连接
                connector.disconnect()
                
        except FirewallConnectionError as e:
            return False, f"连接设备失败: {str(e)}"
        except Exception as e:
            return False, f"回滚过程中发生错误: {str(e)}"
    
    def _create_audit_log(self, policy_id: int, user_id: int, action: str, details: str) -> None:
        """创建审计日志
        
        Args:
            policy_id: 策略ID
            user_id: 用户ID
            action: 操作类型
            details: 详情
        """
        log_data = {
            'policy_id': policy_id,
            'user_id': user_id,
            'action': action,
            'details': details,
            'created_at': datetime.utcnow()
        }
        
        self.audit_repo.create(log_data) 