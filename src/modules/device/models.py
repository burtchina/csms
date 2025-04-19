#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备管理模块数据模型 - 为保持向后兼容而保留
注意: 主要模型已移至 src/models/device.py
"""

# 从新的模型位置导入
from src.models.device import Device, DeviceType, init_device_types

# 保留此文件以确保向后兼容性
# 未来请直接从 src.models.device 导入模型 