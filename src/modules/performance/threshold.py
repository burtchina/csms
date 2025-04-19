#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能阈值管理模块 - 定义性能监控阈值和告警规则
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from src.core.db import db
from src.modules.device.models import Device
from src.modules.performance.models import Alert
from src.models import PerformanceRecord

# 配置日志
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警级别"""
    INFO = "信息"
    WARNING = "警告"
    CRITICAL = "严重"

class ThresholdType(Enum):
    """阈值类型"""
    CPU = "cpu_usage"
    MEMORY = "memory_usage"
    BANDWIDTH = "bandwidth_usage"

class ThresholdRule:
    """阈值规则"""
    
    def __init__(
        self,
        threshold_type: ThresholdType,
        warning_threshold: float,
        critical_threshold: float,
        duration: int = 0,
        device_id: Optional[int] = None,
        enabled: bool = True
    ):
        """
        初始化阈值规则
        
        Args:
            threshold_type: 阈值类型 (CPU, 内存, 带宽)
            warning_threshold: 警告阈值
            critical_threshold: 严重阈值
            duration: 持续时间(秒)，0表示立即触发
            device_id: 设备ID，None表示适用于所有设备
            enabled: 规则是否启用
        """
        self.threshold_type = threshold_type
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.duration = duration
        self.device_id = device_id
        self.enabled = enabled
        self.violation_start_time: Dict[int, datetime] = {}  # 设备ID -> 开始违反阈值的时间

class ThresholdManager:
    """阈值管理器"""
    
    # 默认阈值规则
    default_rules = [
        ThresholdRule(ThresholdType.CPU, 75.0, 90.0, 60),
        ThresholdRule(ThresholdType.MEMORY, 80.0, 95.0, 60),
        ThresholdRule(ThresholdType.BANDWIDTH, 70.0, 90.0, 300)
    ]
    
    # 自定义规则
    custom_rules: List[ThresholdRule] = []
    
    # 告警静默期（秒）- 防止频繁告警
    alert_silence_period = 1800  # 30分钟
    
    # 最后一次告警时间
    last_alert_time: Dict[str, Dict[int, datetime]] = {
        ThresholdType.CPU.value: {},
        ThresholdType.MEMORY.value: {},
        ThresholdType.BANDWIDTH.value: {}
    }
    
    @classmethod
    def add_rule(cls, rule: ThresholdRule):
        """添加自定义规则"""
        cls.custom_rules.append(rule)
        logger.info(f"添加阈值规则: {rule.threshold_type.value}, 警告={rule.warning_threshold}%, 严重={rule.critical_threshold}%")
    
    @classmethod
    def remove_rule(cls, index: int) -> bool:
        """移除自定义规则"""
        if 0 <= index < len(cls.custom_rules):
            rule = cls.custom_rules.pop(index)
            logger.info(f"移除阈值规则: {rule.threshold_type.value}, 设备ID={rule.device_id or '所有'}")
            return True
        return False
    
    @classmethod
    def get_rules(cls) -> List[ThresholdRule]:
        """获取所有规则"""
        return cls.default_rules + cls.custom_rules
    
    @classmethod
    def get_rules_for_device(cls, device_id: int) -> List[ThresholdRule]:
        """获取适用于指定设备的规则"""
        device_rules = [
            rule for rule in cls.custom_rules 
            if rule.enabled and (rule.device_id is None or rule.device_id == device_id)
        ]
        
        # 如果没有设备特定规则，使用默认规则
        if not any(rule.device_id == device_id for rule in device_rules):
            device_rules.extend([rule for rule in cls.default_rules if rule.enabled])
            
        return device_rules
    
    @classmethod
    def check_thresholds(cls, record: PerformanceRecord):
        """
        检查性能记录是否超过阈值
        
        Args:
            record: 性能记录
        """
        device_id = record.device_id
        rules = cls.get_rules_for_device(device_id)
        current_time = datetime.now()
        
        for rule in rules:
            # 获取对应的性能值
            if rule.threshold_type == ThresholdType.CPU:
                value = record.cpu_usage
            elif rule.threshold_type == ThresholdType.MEMORY:
                value = record.memory_usage
            elif rule.threshold_type == ThresholdType.BANDWIDTH:
                value = record.bandwidth_usage
            else:
                continue
            
            # 检查是否超过阈值
            if value >= rule.critical_threshold:
                level = AlertLevel.CRITICAL
                threshold = rule.critical_threshold
            elif value >= rule.warning_threshold:
                level = AlertLevel.WARNING
                threshold = rule.warning_threshold
            else:
                # 如果不超过阈值，重置违反开始时间
                if device_id in rule.violation_start_time:
                    del rule.violation_start_time[device_id]
                continue
            
            # 记录开始违反阈值的时间
            if device_id not in rule.violation_start_time:
                rule.violation_start_time[device_id] = current_time
            
            # 检查是否已经超过持续时间
            violation_duration = (current_time - rule.violation_start_time[device_id]).total_seconds()
            if violation_duration < rule.duration:
                continue
            
            # 检查是否在静默期内
            threshold_type = rule.threshold_type.value
            last_alert = cls.last_alert_time.get(threshold_type, {}).get(device_id)
            if last_alert and (current_time - last_alert).total_seconds() < cls.alert_silence_period:
                continue
            
            # 创建告警
            cls._create_alert(device_id, rule.threshold_type, value, threshold, level)
            
            # 更新最后告警时间
            if threshold_type not in cls.last_alert_time:
                cls.last_alert_time[threshold_type] = {}
            cls.last_alert_time[threshold_type][device_id] = current_time
    
    @classmethod
    def _create_alert(cls, device_id: int, threshold_type: ThresholdType, value: float, 
                      threshold: float, level: AlertLevel):
        """创建告警记录"""
        try:
            device = Device.query.get(device_id)
            if not device:
                logger.error(f"无法创建告警：设备 {device_id} 不存在")
                return
                
            alert_type_map = {
                ThresholdType.CPU: "CPU使用率过高",
                ThresholdType.MEMORY: "内存使用率过高",
                ThresholdType.BANDWIDTH: "带宽使用率过高"
            }
            
            alert_message = f"{alert_type_map.get(threshold_type, '性能告警')}: " \
                           f"当前值 {value:.1f}% 超过阈值 {threshold:.1f}%"
            
            # 创建告警记录
            alert = Alert(
                device_id=device_id,
                alert_type=threshold_type.value,
                alert_level=level.value,
                message=alert_message,
                value=value,
                threshold=threshold,
                created_at=datetime.now(),
                acknowledged=False
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.warning(f"设备 {device.name} [{device_id}] 生成告警: {alert_message}")
            
            # TODO: 可以在这里添加告警通知逻辑（邮件、短信等）
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建告警记录失败: {str(e)}")
    
    @classmethod
    def get_active_alerts(cls, device_id: Optional[int] = None) -> List[Dict]:
        """
        获取活跃告警
        
        Args:
            device_id: 设备ID，None表示获取所有设备的告警
            
        Returns:
            活跃告警列表
        """
        try:
            query = Alert.query.filter_by(acknowledged=False)
            if device_id is not None:
                query = query.filter_by(device_id=device_id)
                
            alerts = query.order_by(Alert.created_at.desc()).all()
            return [alert.to_dict() for alert in alerts]
        except Exception as e:
            logger.error(f"获取活跃告警失败: {str(e)}")
            return []
    
    @classmethod
    def acknowledge_alert(cls, alert_id: int) -> bool:
        """
        确认告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            是否成功确认
        """
        try:
            alert = Alert.query.get(alert_id)
            if not alert:
                return False
                
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            db.session.commit()
            
            logger.info(f"已确认告警 ID: {alert_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"确认告警失败: {str(e)}")
            return False 