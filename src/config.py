#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 配置文件
"""

import os
import secrets
from datetime import timedelta

class Config:
    """基础配置类"""
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    CACHE_REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.example.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@example.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'csms@example.com'
    
    # 设备通信配置
    DEVICE_TIMEOUT = 5  # 设备通信超时时间（秒）
    DEVICE_RETRY = 3    # 设备通信重试次数
    
    # 任务队列配置
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/2'
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小（16MB）
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip'}
    
    # 分页配置
    ITEMS_PER_PAGE = 10
    
    # CSRF保护
    WTF_CSRF_ENABLED = True
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') or False
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 确保使用绝对路径，并创建data目录
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data', 'dev.sqlite')
    WTF_CSRF_ENABLED = False  # 开发环境关闭CSRF保护，方便测试
    LOG_LEVEL = 'DEBUG'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # 确保数据目录存在
        os.makedirs(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data'), exist_ok=True)


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data', 'test.sqlite')
    WTF_CSRF_ENABLED = False  # 测试环境关闭CSRF保护
    CACHE_TYPE = 'simple'     # 测试环境使用简单缓存
    

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data', 'prod.sqlite')
    
    # 生产环境安全设置
    SESSION_COOKIE_SECURE = True       # 仅通过HTTPS发送Cookie
    SESSION_COOKIE_HTTPONLY = True     # 禁止JavaScript访问Cookie
    REMEMBER_COOKIE_SECURE = True      # 仅通过HTTPS发送Remember Cookie
    REMEMBER_COOKIE_HTTPONLY = True    # 禁止JavaScript访问Remember Cookie
    
    # 生产环境性能优化
    SQLALCHEMY_POOL_SIZE = 10          # 连接池大小
    SQLALCHEMY_POOL_TIMEOUT = 30       # 连接超时时间
    SQLALCHEMY_POOL_RECYCLE = 1800     # 连接回收时间
    
    # 生产环境错误邮件通知
    ADMINS = ['admin@example.com']     # 管理员邮箱，用于接收错误报告

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 确保数据和日志目录存在
        data_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data')
        logs_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        # 生产环境错误日志处理
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(os.path.join(logs_dir, 'csms.log'), 
                                          maxBytes=10240, 
                                          backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('校园安全管理系统启动') 