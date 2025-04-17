#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备管理模块初始化
"""

from flask import Blueprint

device_bp = Blueprint('device', __name__, 
                     template_folder='templates')

from src.modules.device import routes 