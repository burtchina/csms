#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSMS 生产环境配置文件
"""

import os
import logging
from datetime import timedelta

class ProductionConfig:
    """生产环境配置类"""
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY')
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  # 生产环境减少会话有效期
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # 数据库连接池大小
        'pool_recycle': 3600,  # 连接回收时间（秒）
        'pool_pre_ping': True  # 连接前检查
    }
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = os.environ.get('REDIS_HOST')
    CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 600  # 缓存超时时间（秒）
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 设备通信配置
    DEVICE_TIMEOUT = 5  # 设备通信超时时间（秒）
    DEVICE_RETRY = 3    # 设备通信重试次数
    
    # 任务队列配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
    CELERY_TASK_EAGER_PROPAGATES = False
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Shanghai'
    
    # 上传文件配置
    UPLOAD_FOLDER = '/app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小（16MB）
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}
    
    # 分页配置
    ITEMS_PER_PAGE = 20  # 生产环境增加每页项目数
    
    # CSRF保护
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF令牌有效期（秒）
    
    # 日志配置
    LOG_TO_STDOUT = True
    LOG_LEVEL = logging.INFO

    # 会话配置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # 将在应用初始化时设置
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = True
    
    # 安全配置
    REMEMBER_COOKIE_SECURE = True  # 仅通过HTTPS发送cookie
    REMEMBER_COOKIE_HTTPONLY = True  # 禁止JavaScript访问cookie
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = 'https'
    
    # 性能监控
    MONITOR_INTERVAL = 300  # 监控数据采集间隔（秒）
    
    @classmethod
    def init_app(cls, app):
        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # 配置日志
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(app.config['LOG_LEVEL'])
            app.logger.addHandler(stream_handler)
        else:
            # 确保日志目录存在
            if not os.path.exists('/app/logs'):
                os.makedirs('/app/logs')
            file_handler = logging.FileHandler('/app/logs/csms.log')
            file_handler.setLevel(app.config['LOG_LEVEL'])
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('CSMS应用启动，生产模式') 