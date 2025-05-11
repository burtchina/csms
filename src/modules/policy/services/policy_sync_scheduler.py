#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略同步调度器
提供策略状态定期同步的调度功能
"""

import logging
import time
import threading
import traceback
import datetime
from typing import Dict, Any, List, Optional

from flask import current_app, has_app_context
from src.core.db import db
from src.modules.policy.services.policy_deploy_service import PolicyDeployService
from src.app import get_app


class PolicySyncScheduler:
    """策略同步调度器，以后台线程方式运行，定期同步策略状态"""
    
    def __init__(self, interval: int = 300, enabled: bool = True):
        """初始化调度器
        
        Args:
            interval: 同步间隔（秒）
            enabled: 是否启用调度器
        """
        self.interval = interval  # 默认5分钟同步一次
        self.enabled = enabled
        self.running = False
        self.thread = None
        self.last_sync_time = None
        self.last_sync_result = None
        self.deploy_service = PolicyDeployService()
        self.failure_count = 0
        self.alert_on_failure = False
        self.alert_threshold = 3
    
    def start(self) -> bool:
        """启动调度器
        
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            logging.warning("策略同步调度器已在运行中")
            return False
        
        if not self.enabled:
            logging.warning("策略同步调度器未启用")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.thread.start()
        
        logging.info(f"策略同步调度器已启动，同步间隔: {self.interval}秒")
        return True
    
    def stop(self) -> bool:
        """停止调度器
        
        Returns:
            bool: 是否成功停止
        """
        if not self.running:
            logging.warning("策略同步调度器未运行")
            return False
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None
        
        logging.info("策略同步调度器已停止")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        status = {
            'enabled': self.enabled,
            'running': self.running,
            'interval': self.interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'last_sync_result': self.last_sync_result,
            'failure_count': self.failure_count,
            'alert_on_failure': self.alert_on_failure,
            'alert_threshold': self.alert_threshold
        }
        
        return status
    
    def set_interval(self, interval: int) -> None:
        """设置同步间隔
        
        Args:
            interval: 同步间隔（秒）
        """
        if interval < 60:
            logging.warning(f"同步间隔太短: {interval}秒，已调整为60秒")
            interval = 60
        
        self.interval = interval
        logging.info(f"策略同步间隔已更新为: {interval}秒")
    
    def force_sync(self) -> Dict[str, Any]:
        """强制执行一次同步
        
        Returns:
            Dict[str, Any]: 同步结果
        """
        logging.info("手动触发策略同步")
        return self._do_sync()
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """更新调度器配置
        
        Args:
            config: 配置字典，包含以下可选参数：
                interval: 同步间隔（秒）
                enabled: 是否启用调度器
                alert_on_failure: 是否在同步失败时发送告警
                alert_threshold: 连续失败多少次后发送告警
        """
        if 'interval' in config:
            self.set_interval(config['interval'])
        
        if 'enabled' in config:
            self.enabled = bool(config['enabled'])
            logging.info(f"策略同步调度器已{'启用' if self.enabled else '禁用'}")
            
            # 如果启用且未运行，则启动调度器
            if self.enabled and not self.running:
                self.start()
            # 如果禁用且正在运行，则停止调度器
            elif not self.enabled and self.running:
                self.stop()
        
        if 'alert_on_failure' in config:
            self.alert_on_failure = bool(config['alert_on_failure'])
            logging.info(f"同步失败告警已{'启用' if self.alert_on_failure else '禁用'}")
        
        if 'alert_threshold' in config:
            self.alert_threshold = max(1, int(config['alert_threshold']))
            logging.info(f"告警阈值已设置为: {self.alert_threshold}次连续失败")
            
    def _handle_sync_failure(self, error: str) -> None:
        """处理同步失败
        
        Args:
            error: 错误信息
        """
        self.failure_count += 1
        logging.error(f"策略同步失败 ({self.failure_count}): {error}")
        
        # 检查是否需要发送告警
        if self.alert_on_failure and self.failure_count >= self.alert_threshold:
            self._send_alert(f"策略同步连续失败{self.failure_count}次，最新错误: {error}")
            # 重置计数器，避免重复告警
            self.failure_count = 0
    
    def _handle_sync_success(self) -> None:
        """处理同步成功"""
        # 如果之前有失败，记录恢复信息
        if self.failure_count > 0:
            logging.info(f"策略同步已恢复正常，之前连续失败{self.failure_count}次")
            
            # 如果配置了告警，发送恢复通知
            if self.alert_on_failure:
                self._send_alert(f"策略同步已恢复正常，之前连续失败{self.failure_count}次")
            
        # 重置失败计数
        self.failure_count = 0
    
    def _send_alert(self, message: str) -> None:
        """发送告警通知
        
        Args:
            message: 告警消息
        """
        # 记录告警日志
        logging.warning(f"策略同步告警: {message}")
        
        try:
            # 这里可以集成实际的告警通知系统，如邮件、短信等
            # 示例：创建系统告警记录
            from flask import current_app
            from src.modules.policy.models.policy_alert import PolicyAlert
            
            # 确保在应用上下文中操作
            with current_app.app_context():
                alert_data = {
                    'policy_id': None,  # 同步告警不针对特定策略
                    'device_id': None,  # 同步告警不针对特定设备
                    'alert_type': 'sync_failure',
                    'severity': 'warning',
                    'details': message,
                    'status': 'new',
                    'created_at': datetime.datetime.now(),
                    'updated_at': datetime.datetime.now()
                }
                
                # 使用数据库会话创建告警
                alert = PolicyAlert(**alert_data)
                db.session.add(alert)
                db.session.commit()
                
                logging.info(f"已创建策略同步告警记录，ID: {alert.id}")
            
        except Exception as e:
            # 不要因为告警失败而影响主流程
            logging.error(f"创建策略同步告警记录失败: {str(e)}")
    
    def _sync_worker(self) -> None:
        """同步工作线程"""
        logging.info("策略同步工作线程已启动")
        
        while self.running:
            try:
                # 执行同步（_do_sync方法内部会自行处理应用上下文）
                self._do_sync()
                
                # 等待下一次同步
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
            
            except Exception as e:
                logging.error(f"策略同步过程中发生错误: {str(e)}")
                logging.debug(traceback.format_exc())
                
                # 出错后等待一分钟再重试
                time.sleep(60)
        
        logging.info("策略同步工作线程已退出")
    
    def _do_sync(self) -> Dict[str, Any]:
        """执行一次同步操作
        
        Returns:
            Dict[str, Any]: 同步结果
        """
        start_time = time.time()
        self.last_sync_time = datetime.datetime.now()
        
        try:
            # 导入Flask应用
            from flask import current_app, has_app_context
            
            # 检查是否有应用上下文，如果没有则创建一个
            if not has_app_context():
                # 尝试从全局获取Flask应用实例
                app = get_app()
                if not app:
                    logging.error("无法进行策略同步：无法获取应用实例")
                    return {
                        'error': '无应用实例',
                        'sync_time': self.last_sync_time.isoformat(),
                        'elapsed_time': f"{time.time() - start_time:.2f}秒",
                        'success': 0,
                        'failed': 0,
                        'not_found': 0
                    }
                
                # 创建应用上下文
                with app.app_context():
                    return self._execute_sync(start_time)
            else:
                # 已有应用上下文，直接执行同步
                return self._execute_sync(start_time)
        
        except Exception as e:
            error_result = {
                'error': str(e),
                'sync_time': self.last_sync_time.isoformat(),
                'elapsed_time': f"{time.time() - start_time:.2f}秒",
                'success': 0,
                'failed': 0,
                'not_found': 0
            }
            
            self.last_sync_result = error_result
            
            # 处理同步异常
            self._handle_sync_failure(str(e))
            
            logging.error(f"策略同步失败: {str(e)}")
            logging.debug(traceback.format_exc())
            
            return error_result
    
    def _execute_sync(self, start_time: float) -> Dict[str, Any]:
        """在应用上下文中执行同步操作
        
        Args:
            start_time: 同步开始时间
            
        Returns:
            Dict[str, Any]: 同步结果
        """
        try:
            # 创建新的数据库会话
            session = db.create_scoped_session()
            deploy_service = PolicyDeployService()
            
            # 执行同步
            result = deploy_service.sync_policy_status()
            
            # 记录结果
            elapsed = time.time() - start_time
            result['elapsed_time'] = f"{elapsed:.2f}秒"
            result['sync_time'] = self.last_sync_time.isoformat()
            
            self.last_sync_result = result
            
            logging.info(f"策略同步完成，耗时: {elapsed:.2f}秒，成功: {result['success']}，"
                        f"失败: {result['failed']}，未找到: {result['not_found']}")
            
            # 处理同步成功
            if result['failed'] == 0:
                self._handle_sync_success()
            else:
                self._handle_sync_failure(f"同步部分失败: {result['failed']}个策略同步失败")
            
            return result
        
        finally:
            # 如果创建了新会话，关闭它
            if 'session' in locals():
                session.close()


# 全局调度器实例
_scheduler_instance = None


def get_scheduler() -> PolicySyncScheduler:
    """获取全局调度器实例
    
    Returns:
        PolicySyncScheduler: 调度器实例
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PolicySyncScheduler()
    
    return _scheduler_instance 