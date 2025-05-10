#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强版设备监控服务，基于SSH监控模块提供更高级的设备性能监控功能
"""

import time
import threading
import queue
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.core.db import db
from src.models.device import Device
from src.models.performance import PerformanceData
from src.modules.performance.enhanced_ssh_monitor import (
    get_connection,
    get_cpu_usage,
    get_memory_usage,
    get_uptime,
    get_interface_stats,
    collect_device_data,
    close_connection,
    close_all_connections,
    send_command,
    get_device_status,
    get_all_connections_status
)

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量
monitor_threads = {}  # 存储设备监控线程 {device_id: thread}
keepalive_threads = {}  # 存储保活线程 {device_id: thread}
device_performance_data = {}  # 存储设备性能数据队列 {device_id: queue.Queue}
latest_device_data = {}  # 存储设备最新数据 {device_id: data_dict}
monitor_stop_flags = {}  # 控制监控线程停止的标志 {device_id: bool}

class EnhancedMonitorService:
    """增强版设备监控服务"""
    
    @staticmethod
    def start_device_monitoring(device_id: int) -> Dict:
        """
        启动设备性能监控
        
        Args:
            device_id: 设备ID
            
        Returns:
            状态和消息
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: ID={device_id}'}
                
            # 检查是否已在监控中
            if device_id in monitor_threads and monitor_threads[device_id].is_alive():
                return {'status': 'success', 'message': f'设备 {device.name} 已在监控中'}
                
            # 初始化数据队列
            if device_id not in device_performance_data:
                device_performance_data[device_id] = queue.Queue(maxsize=100)
                
            # 初始化最新数据
            latest_device_data[device_id] = {
                "cpu_usage": 0,
                "memory_usage": 0,
                "bandwidth_usage": 0,
                "uptime": "正在连接...",
                "timestamp": time.time(),
                "interfaces": {}
            }
            
            # 初始化停止标志
            monitor_stop_flags[device_id] = False
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=EnhancedMonitorService._monitor_device_thread,
                args=(device_id,),
                daemon=True
            )
            monitor_threads[device_id] = monitor_thread
            monitor_thread.start()
            
            # 启动保活线程
            keepalive_thread = threading.Thread(
                target=EnhancedMonitorService._keepalive_thread,
                args=(device_id,),
                daemon=True
            )
            keepalive_threads[device_id] = keepalive_thread
            keepalive_thread.start()
            
            logger.info(f"已启动对设备 {device.name} 的性能监控")
            return {'status': 'success', 'message': f'已启动对设备 {device.name} 的性能监控'}
            
        except Exception as e:
            logger.error(f"启动监控出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'启动监控出错: {str(e)}'}
    
    @staticmethod
    def stop_device_monitoring(device_id: int) -> Dict:
        """
        停止设备性能监控
        
        Args:
            device_id: 设备ID
            
        Returns:
            状态和消息
        """
        try:
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: ID={device_id}'}
                
            # 设置停止标志
            monitor_stop_flags[device_id] = True
            
            # 关闭设备连接
            close_connection(device_id)
            
            # 清理数据队列
            if device_id in device_performance_data:
                del device_performance_data[device_id]
                
            # 清理最新数据
            if device_id in latest_device_data:
                del latest_device_data[device_id]
                
            # 等待线程结束（最多等待5秒）
            if device_id in monitor_threads:
                monitor_threads[device_id].join(timeout=5)
                
            if device_id in keepalive_threads:
                keepalive_threads[device_id].join(timeout=5)
                
            logger.info(f"已停止对设备 {device.name} 的性能监控")
            return {'status': 'success', 'message': f'已停止对设备 {device.name} 的性能监控'}
            
        except Exception as e:
            logger.error(f"停止监控出错: {str(e)}")
            return {'status': 'error', 'message': f'停止监控出错: {str(e)}'}
    
    @staticmethod
    def get_latest_data(device_id: int) -> Dict:
        """
        获取设备最新性能数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            最新性能数据
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: ID={device_id}'}
                
            # 检查是否已启动监控
            if device_id not in latest_device_data:
                # 如果未启动监控，自动创建模拟数据
                cpu_usage = round(random.uniform(20.0, 80.0), 1)
                memory_usage = round(random.uniform(30.0, 70.0), 1)
                bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
                
                latest_device_data[device_id] = {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "bandwidth_usage": bandwidth_usage,
                    "uptime": "系统启动中...",
                    "timestamp": time.time(),
                    "interfaces": {},
                    "connection_status": {
                        "status": "disconnected",
                        "connected": False
                    }
                }
                
                # 自动启动监控
                EnhancedMonitorService.start_device_monitoring(device_id)
                
            # 返回最新数据
            return {
                'status': 'success',
                'data': latest_device_data[device_id],
                'device_name': device.name
            }
            
        except Exception as e:
            logger.error(f"获取最新数据出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'获取最新数据出错: {str(e)}'}
    
    @staticmethod
    def get_history_data(device_id: int) -> Dict:
        """
        获取设备历史性能数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            历史性能数据
        """
        try:
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: ID={device_id}'}
                
            if device_id not in device_performance_data:
                return {'status': 'error', 'message': f'设备 {device.name} 未在监控中'}
                
            # 从队列中提取数据
            queue_obj = device_performance_data[device_id]
            history_data = list(queue_obj.queue)
            
            return {
                'status': 'success',
                'data': history_data,
                'device_name': device.name
            }
            
        except Exception as e:
            logger.error(f"获取历史数据出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'status': 'error', 'message': f'获取历史数据出错: {str(e)}'}
    
    @staticmethod
    def save_performance_data(device_id: int, data: Dict) -> Optional[Dict]:
        """
        保存性能数据到数据库
        
        Args:
            device_id: 设备ID
            data: 性能数据
            
        Returns:
            保存的性能数据记录ID，失败时返回None
        """
        try:
            # 准备数据
            cpu_usage = data.get('cpu_usage', 0)
            memory_usage = data.get('memory_usage', 0)
            bandwidth_usage = data.get('bandwidth_usage', 0)
            uptime = data.get('uptime', 'Unknown')
            timestamp = datetime.now()
            
            # 使用SQL语句直接插入数据
            sql = """
            INSERT INTO performance_data 
            (device_id, cpu_usage, memory_usage, bandwidth_usage, uptime, timestamp, created_at, updated_at) 
            VALUES (:device_id, :cpu_usage, :memory_usage, :bandwidth_usage, :uptime, :timestamp, :created_at, :updated_at)
            """
            
            result = db.session.execute(sql, {
                'device_id': device_id,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'bandwidth_usage': bandwidth_usage,
                'uptime': uptime,
                'timestamp': timestamp,
                'created_at': timestamp,
                'updated_at': timestamp
            })
            
            db.session.commit()
            
            logger.debug(f"已保存设备 {device_id} 的性能数据: CPU={cpu_usage}%, MEM={memory_usage}%")
            return {'id': result.lastrowid, 'device_id': device_id, 'timestamp': timestamp}
            
        except Exception as e:
            logger.error(f"保存性能数据失败: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def execute_command(device_id: int, command: str) -> Dict:
        """
        执行自定义命令
        
        Args:
            device_id: 设备ID
            command: 要执行的命令
            
        Returns:
            命令执行结果
        """
        try:
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: ID={device_id}'}
                
            # 发送命令
            result = send_command(device_id, command)
            
            if result['status'] == 'success':
                logger.info(f"设备 {device.name} 执行命令 '{command}' 成功")
            else:
                logger.warning(f"设备 {device.name} 执行命令 '{command}' 失败: {result['message']}")
                
            return {
                'status': result['status'],
                'message': result['message'],
                'output': result['output'],
                'device_name': device.name,
                'command': command
            }
            
        except Exception as e:
            logger.error(f"执行命令出错: {str(e)}")
            return {'status': 'error', 'message': f'执行命令出错: {str(e)}'}
    
    @staticmethod
    def get_all_monitored_devices() -> List[Dict]:
        """
        获取所有正在监控的设备信息
        
        Returns:
            设备信息列表
        """
        result = []
        for device_id in monitor_threads:
            try:
                device = Device.query.get(device_id)
                if device:
                    # 获取最新数据
                    latest_data = latest_device_data.get(device_id, {})
                    
                    # 获取连接状态
                    connection_status = latest_data.get('connection_status', {
                        'status': 'unknown',
                        'connected': False
                    })
                    
                    result.append({
                        'id': device_id,
                        'name': device.name,
                        'ip_address': device.ip_address,
                        'type': device.type.name if device.type else 'Unknown',
                        'status': device.status,
                        'monitoring': monitor_threads[device_id].is_alive(),
                        'connection_status': connection_status,
                        'cpu_usage': latest_data.get('cpu_usage', 0),
                        'memory_usage': latest_data.get('memory_usage', 0)
                    })
            except Exception as e:
                logger.error(f"获取设备 {device_id} 信息出错: {str(e)}")
                
        return result
    
    @staticmethod
    def _monitor_device_thread(device_id: int):
        """
        设备监控线程
        
        Args:
            device_id: 设备ID
        """
        # 导入当前应用，并创建应用上下文
        from flask import current_app
        from src.app import create_app
        
        # 创建应用实例并推送上下文
        app = create_app()
        
        with app.app_context():
            try:
                # 获取设备信息
                device_info = db.session.execute(
                    f"SELECT id, name, ip_address, username, password, port FROM devices WHERE id = {device_id}"
                ).fetchone()
                
                if not device_info:
                    logger.error(f"设备不存在: ID={device_id}")
                    return
                    
                device_name = device_info.name
                logger.info(f"启动设备 {device_name} (ID:{device_id}) 的性能监控线程")
                
                # 监控间隔
                cpu_memory_interval = 10  # 默认10秒
                interface_stats_interval = 30  # 接口统计数据收集间隔30秒
                save_db_interval = 300  # 保存到数据库间隔5分钟
                
                # 上次数据收集时间
                last_cpu_memory_time = 0
                last_interface_stats_time = 0
                last_save_db_time = 0
                
                # 设备连接信息
                device_ip = device_info.ip_address
                device_username = device_info.username or 'admin'
                device_password = device_info.password or 'admin123'
                device_port = device_info.port or 22
                
                logger.debug(f"设备连接信息: IP={device_ip}, 用户名={device_username}, 端口={device_port}")
                
                # 监控循环
                while not monitor_stop_flags.get(device_id, False):
                    current_time = time.time()
                    
                    try:
                        # 获取基本性能数据（每cpu_memory_interval秒）
                        if current_time - last_cpu_memory_time >= cpu_memory_interval:
                            # 收集设备数据
                            data = collect_device_data(
                                device_id, 
                                device_ip, 
                                device_username, 
                                device_password, 
                                device_port
                            )
                            
                            # 更新最新数据
                            latest_device_data[device_id] = data
                            
                            # 添加到历史数据队列
                            if device_id in device_performance_data:
                                if device_performance_data[device_id].full():
                                    # 队列满则移除最旧的数据
                                    try:
                                        device_performance_data[device_id].get_nowait()
                                    except:
                                        pass
                                    
                                try:
                                    device_performance_data[device_id].put_nowait(data)
                                except:
                                    pass
                            
                            # 更新时间戳
                            last_cpu_memory_time = current_time
                            
                            logger.debug(f"设备 {device_name} 数据更新: CPU={data.get('cpu_usage')}%, MEM={data.get('memory_usage')}%")
                            
                        # 保存到数据库（每save_db_interval秒）
                        if current_time - last_save_db_time >= save_db_interval:
                            if device_id in latest_device_data:
                                EnhancedMonitorService.save_performance_data(
                                    device_id, 
                                    latest_device_data[device_id]
                                )
                                last_save_db_time = current_time
                        
                        # 休眠一小段时间，减少CPU使用
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"监控设备 {device_name} 出错: {str(e)}")
                        time.sleep(30)  # 出错后等待30秒再重试
                        
                logger.info(f"设备 {device_name} 监控线程已停止")
                
            except Exception as e:
                logger.error(f"监控线程异常: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
    
    @staticmethod
    def _keepalive_thread(device_id: int):
        """
        保持连接的线程
        
        Args:
            device_id: 设备ID
        """
        # 导入当前应用，并创建应用上下文
        from flask import current_app
        from src.app import create_app
        
        # 创建应用实例并推送上下文
        app = create_app()
        
        with app.app_context():
            try:
                # 获取设备信息
                device_info = db.session.execute(
                    f"SELECT id, name FROM devices WHERE id = {device_id}"
                ).fetchone()
                
                if not device_info:
                    logger.error(f"设备不存在: ID={device_id}")
                    return
                    
                device_name = device_info.name
                logger.info(f"启动设备 {device_name} (ID:{device_id}) 的保活线程")
                
                # 保活间隔
                keepalive_interval = 60  # 默认60秒
                
                # 监控循环
                while not monitor_stop_flags.get(device_id, False):
                    try:
                        # 发送保活命令
                        result = send_command(device_id, "display clock")
                        
                        if result['status'] == 'success':
                            logger.debug(f"设备 {device_name} 保活成功: {result['output']}")
                        else:
                            logger.warning(f"设备 {device_name} 保活失败: {result['message']}")
                            
                        # 休眠一段时间
                        time.sleep(keepalive_interval)
                        
                    except Exception as e:
                        logger.error(f"保活设备 {device_name} 出错: {str(e)}")
                        time.sleep(30)  # 出错后等待30秒再重试
                        
                logger.info(f"设备 {device_name} 保活线程已停止")
                
            except Exception as e:
                logger.error(f"保活线程异常: {str(e)}") 