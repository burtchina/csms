#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据模型包 - 导出所有模型
"""

# 导入设备相关模型
from src.models.device import Device, DeviceType

# 导入性能相关模型
from src.models.performance import PerformanceRecord, Threshold

# 后续添加其他模型导入
# from .user import User, Role

# 导出所有模型
__all__ = [
    'Device', 
    'DeviceType',
    'PerformanceRecord',
    'Threshold'
]  # 后续添加更多模型 