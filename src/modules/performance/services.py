#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能监控服务层，提供性能数据采集和分析功能
"""

import time
import logging
import random
import sys
import threading
import queue
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

# 确保Python能找到pysnmp包
try:
    # 获取site-packages路径
    import site
    site_packages = site.getsitepackages()
    # 添加到系统路径
    for path in site_packages:
        if path not in sys.path:
            sys.path.append(path)
except Exception as e:
    logging.warning(f"调整Python路径失败: {str(e)}")

try:
    from netmiko import ConnectHandler
    import paramiko
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    logging.warning("Netmiko未安装，将使用模拟数据")

# 使用SNMP辅助模块代替直接导入PySnmp
try:
    from src.core.snmp_helper import (
        get_snmp_data, 
        get_snmp_bulk, 
        snmp_walk, 
        SNMP_AVAILABLE
    )
    if SNMP_AVAILABLE:
        logging.info("成功导入SNMP辅助模块，SNMP功能可用")
    else:
        logging.warning("SNMP辅助模块已导入，但PySnmp不可用，将使用模拟数据")
except ImportError as e:
    SNMP_AVAILABLE = False
    logging.warning(f"导入SNMP辅助模块失败: {str(e)}，将使用模拟数据")

from src.db import db
from src.core.models import Device, PerformanceRecord, Threshold, Alert

# 创建日志器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设备监控数据存储
device_performance_data = {}  # 格式: {device_id: queue.Queue}
latest_device_data = {}  # 格式: {device_id: {...}}

# 连接锁，防止多线程同时操作连接
connection_locks = {}  # 格式: {device_id: threading.Lock()}

# 当前连接对象
device_connections = {}  # 格式: {device_id: connection_object}

# 上次连接时间
last_connection_times = {}  # 格式: {device_id: timestamp}

# 监控线程
monitor_threads = {}  # 格式: {device_id: thread}

# 保活线程
keepalive_threads = {}  # 格式: {device_id: thread}

class RealTimeMonitor:
    """设备实时监控服务"""
    
    @staticmethod
    def start_device_monitoring(device_id: int) -> Dict:
        """
        启动对指定设备的实时监控
        
        Args:
            device_id: 设备ID
            
        Returns:
            启动结果
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
            
            # 如果已经在监控中，则返回成功
            if device_id in monitor_threads and monitor_threads[device_id].is_alive():
                return {'status': 'success', 'message': f'设备 {device.name} 已在监控中'}
                
            # 创建数据队列
            if device_id not in device_performance_data:
                device_performance_data[device_id] = queue.Queue(maxsize=100)
                
            # 创建连接锁
            if device_id not in connection_locks:
                connection_locks[device_id] = threading.Lock()
                
            # 初始化最新数据
            latest_device_data[device_id] = {
                "cpu_usage": 0,
                "memory_usage": 0,
                "bandwidth_usage": 0,
                "uptime": "",
                "timestamp": time.time(),
                "interfaces": {}
            }
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=RealTimeMonitor._monitor_device_performance,
                args=(device_id,),
                daemon=True
            )
            monitor_threads[device_id] = monitor_thread
            monitor_thread.start()
            
            # 启动保活线程
            keepalive_thread = threading.Thread(
                target=RealTimeMonitor._keepalive_thread,
                args=(device_id,),
                daemon=True
            )
            keepalive_threads[device_id] = keepalive_thread
            keepalive_thread.start()
            
            logger.info(f"已启动对设备 {device.name} 的实时监控")
            return {'status': 'success', 'message': f'已启动对设备 {device.name} 的实时监控'}
            
        except Exception as e:
            logger.error(f"启动设备监控失败: {str(e)}")
            return {'status': 'error', 'message': f'启动设备监控失败: {str(e)}'}
    
    @staticmethod
    def stop_device_monitoring(device_id: int) -> Dict:
        """
        停止对指定设备的实时监控
        
        Args:
            device_id: 设备ID
            
        Returns:
            停止结果
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
                
            # 清理连接
            if device_id in device_connections:
                with connection_locks.get(device_id, threading.Lock()):
                    if device_connections.get(device_id):
                        try:
                            device_connections[device_id].disconnect()
                        except:
                            pass
                        device_connections[device_id] = None
            
            # 线程会自动终止(daemon=True)
            if device_id in monitor_threads:
                del monitor_threads[device_id]
                
            if device_id in keepalive_threads:
                del keepalive_threads[device_id]
                
            logger.info(f"已停止对设备 {device.name} 的实时监控")
            return {'status': 'success', 'message': f'已停止对设备 {device.name} 的实时监控'}
            
        except Exception as e:
            logger.error(f"停止设备监控失败: {str(e)}")
            return {'status': 'error', 'message': f'停止设备监控失败: {str(e)}'}
    
    @staticmethod
    def get_latest_data(device_id: int) -> Dict:
        """
        获取设备的最新性能数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            最新性能数据
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
                
            # 检查是否已启动监控
            if device_id not in latest_device_data:
                return {'status': 'error', 'message': f'设备 {device.name} 未启动监控'}
                
            # 返回最新数据
            return {
                'status': 'success',
                'data': latest_device_data[device_id],
                'device_name': device.name
            }
            
        except Exception as e:
            logger.error(f"获取最新数据失败: {str(e)}")
            return {'status': 'error', 'message': f'获取最新数据失败: {str(e)}'}
    
    @staticmethod
    def get_history_data(device_id: int) -> Dict:
        """
        获取设备的历史性能数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            历史性能数据
        """
        try:
            # 检查设备是否存在
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
                
            # 检查是否已启动监控
            if device_id not in device_performance_data:
                return {'status': 'error', 'message': f'设备 {device.name} 未启动监控'}
                
            # 获取历史数据
            history = list(device_performance_data[device_id].queue)
            
            return {
                'status': 'success',
                'data': history,
                'device_name': device.name
            }
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            return {'status': 'error', 'message': f'获取历史数据失败: {str(e)}'}
    
    @staticmethod
    def _get_connection(device_id: int):
        """获取或创建设备连接"""
        global device_connections, last_connection_times
        
        # 获取设备信息
        device = Device.query.get(device_id)
        if not device:
            raise ValueError(f"设备不存在: {device_id}")
            
        with connection_locks.get(device_id, threading.Lock()):
            # 检查连接是否存在且有效
            if device_id in device_connections and device_connections[device_id] is not None:
                try:
                    # 发送简单命令测试连接是否有效
                    if hasattr(device_connections[device_id], 'find_prompt'):
                        device_connections[device_id].find_prompt()
                    return device_connections[device_id]
                except Exception as e:
                    logger.warning(f"连接已失效，准备重新连接: {str(e)}")
                    try:
                        device_connections[device_id].disconnect()
                    except:
                        pass
                    device_connections[device_id] = None
            
            # 连接不存在或无效，创建新连接
            # 检查是否频繁重连（防止在短时间内多次重连）
            current_time = time.time()
            if device_id in last_connection_times and current_time - last_connection_times.get(device_id, 0) < 5:
                time.sleep(5)  # 等待一段时间再重连
            
            # 检查是否有netmiko支持
            if not NETMIKO_AVAILABLE:
                logger.warning("Netmiko未安装，无法连接设备")
                return None
                
            try:
                logger.info(f"创建到设备 {device.name} 的新连接...")
                
                # 设置连接参数
                device_info = {
                    'device_type': 'huawei',  # 默认使用华为设备
                    'ip': device.ip_address,
                    'username': 'admin',  # 默认用户名，实际应用中应从配置读取
                    'password': 'admin123',  # 默认密码，实际应用中应从配置读取
                    'port': 22,  # 默认SSH端口
                    'timeout': 10,
                    'keepalive': 30,
                    'session_timeout': 60,
                    'auto_connect': True,
                    'global_delay_factor': 2
                }
                
                # 创建SSH客户端
                ssh_conn = paramiko.SSHClient()
                ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 使用ConnectHandler连接设备
                conn = ConnectHandler(**device_info)
                
                # 发送一个简单命令确认连接正常
                conn.find_prompt()
                
                device_connections[device_id] = conn
                last_connection_times[device_id] = time.time()
                logger.info(f"成功建立到设备 {device.name} 的新连接")
                
                # 发送keep-alive配置命令（如果设备支持）
                try:
                    conn.send_command("screen-length 0 temporary")  # 禁用分页
                except:
                    pass
                    
                return conn
            except Exception as e:
                logger.error(f"创建连接失败: {str(e)}")
                # 如果连接失败，返回None
                return None
    
    @staticmethod
    def _monitor_device_performance(device_id: int):
        """后台线程：持续监控设备性能"""
        # 获取设备信息
        device = Device.query.get(device_id)
        if not device:
            logger.error(f"设备不存在: {device_id}")
            return
            
        # 设置监控间隔（秒）
        cpu_memory_interval = 10  # CPU和内存每10秒查询一次
        interface_interval = 30   # 接口信息每30秒查询一次
        
        last_interface_check = 0
        
        while True:
            try:
                # 如果无法使用netmiko，使用模拟数据
                if not NETMIKO_AVAILABLE:
                    # 生成模拟数据
                    cpu_usage = round(random.uniform(20.0, 80.0), 1)
                    memory_usage = round(random.uniform(30.0, 70.0), 1)
                    bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
                    uptime = "1 week, 3 days, 12 hours, 36 minutes"
                    interfaces = {
                        "GigabitEthernet0/0/1": {
                            "status": "up", 
                            "input_rate": random.randint(1000, 10000000),
                            "output_rate": random.randint(1000, 10000000)
                        },
                        "GigabitEthernet0/0/2": {
                            "status": "up", 
                            "input_rate": random.randint(1000, 10000000),
                            "output_rate": random.randint(1000, 10000000)
                        }
                    }
                else:
                    # 1. 获取CPU和内存使用率
                    cpu_usage = RealTimeMonitor._get_cpu_usage(device_id)
                    memory_usage = RealTimeMonitor._get_memory_usage(device_id)
                    
                    # 简单的带宽使用率估计（实际应基于接口流量计算）
                    bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
                    
                    # 2. 获取运行时间
                    uptime = RealTimeMonitor._get_uptime(device_id)
                    
                    # 3. 只在特定间隔获取接口信息（减少请求频率）
                    current_time = time.time()
                    if current_time - last_interface_check >= interface_interval:
                        interfaces = RealTimeMonitor._get_interface_stats(device_id)
                        last_interface_check = current_time
                    else:
                        # 重用上次的接口信息
                        interfaces = latest_device_data.get(device_id, {}).get('interfaces', {})
                
                # 更新最新数据
                timestamp = time.time()
                data = {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "bandwidth_usage": bandwidth_usage,
                    "uptime": uptime,
                    "interfaces": interfaces,
                    "timestamp": timestamp
                }
                
                latest_device_data[device_id] = data
                
                # 将数据保存到数据库
                try:
                    record = PerformanceRecord(
                        device_id=device_id,
                        cpu_usage=cpu_usage,
                        memory_usage=memory_usage,
                        bandwidth_usage=bandwidth_usage,
                        recorded_at=datetime.now()
                    )
                    db.session.add(record)
                    db.session.commit()
                    
                    # 检查是否超过阈值
                    ThresholdManager.check_thresholds(record)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"保存性能记录失败: {str(e)}")
                
                # 将数据放入队列
                if device_id in device_performance_data:
                    queue_obj = device_performance_data[device_id]
                    if queue_obj.full():
                        queue_obj.get()  # 移除最旧的数据
                    queue_obj.put(data)
                
                logger.info(f"设备 {device.name} 性能数据: CPU {cpu_usage}%, 内存 {memory_usage}%")
                
                # 按照设定的间隔时间休眠
                time.sleep(cpu_memory_interval)
                
            except Exception as e:
                logger.error(f"监控设备 {device.name} 过程中出错: {str(e)}")
                
                # 清理连接
                if device_id in device_connections:
                    with connection_locks.get(device_id, threading.Lock()):
                        if device_connections.get(device_id):
                            try:
                                device_connections[device_id].disconnect()
                            except:
                                pass
                            device_connections[device_id] = None
                
                # 休眠一段时间再重试
                time.sleep(10)
    
    @staticmethod
    def _keepalive_thread(device_id: int):
        """保持SSH连接活跃的线程"""
        # 获取设备信息
        device = Device.query.get(device_id)
        if not device:
            logger.error(f"设备不存在: {device_id}")
            return
            
        while True:
            try:
                # 每25秒发送一个简单的保活命令
                if device_id in device_connections and device_connections[device_id] is not None:
                    with connection_locks.get(device_id, threading.Lock()):
                        if device_connections.get(device_id):
                            try:
                                # 发送对设备影响最小的命令
                                device_connections[device_id].send_command(" ")
                                logger.debug(f"向设备 {device.name} 发送保活信号")
                            except Exception as e:
                                logger.warning(f"设备 {device.name} 保活失败: {str(e)}")
            except Exception as e:
                logger.warning(f"设备 {device.name} 保活线程错误: {str(e)}")
            
            # 等待下一次保活
            time.sleep(25)
    
    @staticmethod
    def _get_cpu_usage(device_id: int) -> float:
        """获取CPU使用率"""
        try:
            conn = RealTimeMonitor._get_connection(device_id)
            if not conn:
                return 0.0
                
            output = conn.send_command('display cpu-usage')
            match = re.search(r'CPU Usage\s+:\s+(\d+)%', output)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def _get_memory_usage(device_id: int) -> float:
        """获取内存使用率"""
        try:
            conn = RealTimeMonitor._get_connection(device_id)
            if not conn:
                return 0.0
                
            output = conn.send_command('display memory-usage')
            match = re.search(r'Memory utilization\s+:\s+(\d+)%', output)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception as e:
            logger.error(f"获取内存使用率失败: {str(e)}")
            return 0.0
    
    @staticmethod
    def _get_uptime(device_id: int) -> str:
        """获取设备运行时间"""
        try:
            conn = RealTimeMonitor._get_connection(device_id)
            if not conn:
                return "Unknown"
                
            output = conn.send_command('display version')
            match = re.search(r'Uptime is\s+(.+)', output)
            if match:
                return match.group(1)
            return "Unknown"
        except Exception as e:
            logger.error(f"获取设备运行时间失败: {str(e)}")
            return "Unknown"
    
    @staticmethod
    def _get_interface_stats(device_id: int) -> Dict:
        """获取接口统计信息"""
        interfaces = {}
        
        try:
            conn = RealTimeMonitor._get_connection(device_id)
            if not conn:
                return interfaces
                
            # 1. 获取接口列表
            output = conn.send_command('display interface brief')
            
            # 解析接口信息
            for line in output.splitlines():
                if 'GigabitEthernet' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        interface_name = parts[0]
                        status = "up" if "up" in line.lower() and "down" not in line.lower() else "down"
                        interfaces[interface_name] = {"status": status}
            
            # 2. 仅获取UP状态接口的流量信息（最多3个）
            up_interfaces = [intf for intf, data in interfaces.items() if data['status'] == 'up']
            for interface in up_interfaces[:3]:  # 限制只检查前3个UP状态的接口
                try:
                    output = conn.send_command(f'display interface {interface}')
                    
                    # 提取输入/输出速率
                    input_match = re.search(r'input.+?(\d+)\s+bits/sec', output, re.DOTALL)
                    output_match = re.search(r'output.+?(\d+)\s+bits/sec', output, re.DOTALL)
                    
                    input_rate = int(input_match.group(1)) if input_match else 0
                    output_rate = int(output_match.group(1)) if output_match else 0
                    
                    interfaces[interface]["input_rate"] = input_rate
                    interfaces[interface]["output_rate"] = output_rate
                except Exception as e:
                    logger.error(f"获取接口 {interface} 信息时出错: {str(e)}")
        except Exception as e:
            logger.error(f"获取接口统计信息失败: {str(e)}")
        
        return interfaces

class PerformanceCollector:
    """性能数据采集服务"""
    
    @staticmethod
    def collect_device_performance(device_id: int) -> Dict:
        """
        采集指定设备的性能数据
        
        Args:
            device_id: 设备ID
            
        Returns:
            采集结果字典
        """
        try:
            # 获取设备信息
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
            
            # 尝试使用SNMP获取真实数据
            if SNMP_AVAILABLE:
                try:
                    # 定义SNMP参数
                    community = 'public'  # 默认community，实际应用中应从配置读取
                    ip_address = device.ip_address
                    
                    # 获取CPU使用率 - 华为设备OID
                    cpu_usage = PerformanceCollector.get_snmp_data(ip_address, community, '1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5.0')
                    if cpu_usage is None:
                        # 尝试通用OID
                        cpu_usage = PerformanceCollector.get_snmp_data(ip_address, community, '1.3.6.1.4.1.9.9.109.1.1.1.1.5.1')
                    
                    # 获取内存使用率 - 华为设备OID
                    memory_usage = PerformanceCollector.get_snmp_data(ip_address, community, '1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7.0')
                    if memory_usage is None:
                        # 尝试通用OID
                        memory_usage = PerformanceCollector.get_snmp_data(ip_address, community, '1.3.6.1.4.1.9.9.48.1.1.1.5.1')
                    
                    # 获取带宽使用率 - 需要计算
                    bandwidth_usage = PerformanceCollector.get_bandwidth_usage(ip_address, community)
                    
                    # 转换为浮点数
                    cpu_usage = float(cpu_usage) if cpu_usage is not None else None
                    memory_usage = float(memory_usage) if memory_usage is not None else None
                    bandwidth_usage = float(bandwidth_usage) if bandwidth_usage is not None else None
                    
                    # 如果无法获取真实数据，使用模拟数据
                    if cpu_usage is None:
                        logger.warning(f"无法通过SNMP获取设备 {device.name} 的CPU使用率，将使用模拟数据")
                        cpu_usage = round(random.uniform(20.0, 80.0), 1)
                        
                    if memory_usage is None:
                        logger.warning(f"无法通过SNMP获取设备 {device.name} 的内存使用率，将使用模拟数据")
                        memory_usage = round(random.uniform(30.0, 70.0), 1)
                        
                    if bandwidth_usage is None:
                        logger.warning(f"无法通过SNMP获取设备 {device.name} 的带宽使用率，将使用模拟数据")
                        bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
                except Exception as e:
                    logger.error(f"SNMP获取数据出错: {str(e)}，将使用模拟数据")
                    # 出错时使用模拟数据
                    cpu_usage = round(random.uniform(20.0, 80.0), 1)
                    memory_usage = round(random.uniform(30.0, 70.0), 1)
                    bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
            else:
                # 如果未安装pysnmp，使用模拟数据
                logger.warning("PySnmp未安装，使用模拟数据")
                cpu_usage = round(random.uniform(20.0, 80.0), 1)
                memory_usage = round(random.uniform(30.0, 70.0), 1)
                bandwidth_usage = round(random.uniform(10.0, 60.0), 1)
                
            # 创建性能记录
            record = PerformanceRecord(
                device_id=device_id,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                bandwidth_usage=bandwidth_usage,
                recorded_at=datetime.now()
            )
            
            # 保存到数据库
            db.session.add(record)
            db.session.commit()
            
            # 检查是否超过阈值
            alerts = ThresholdManager.check_thresholds(record)
            
            return {
                'status': 'success',
                'device_id': device_id,
                'device_name': device.name,
                'performance': {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'bandwidth_usage': bandwidth_usage,
                    'recorded_at': record.recorded_at.strftime('%Y-%m-%d %H:%M:%S')
                },
                'alerts': alerts
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"数据库错误: {str(e)}")
            return {'status': 'error', 'message': f'数据库错误: {str(e)}'}
        except Exception as e:
            logger.error(f"采集性能数据出错: {str(e)}")
            return {'status': 'error', 'message': f'采集性能数据出错: {str(e)}'}
            
    @staticmethod
    def get_snmp_data(ip, community, oid):
        """通过SNMP获取数据"""
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                      CommunityData(community),
                      UdpTransportTarget((ip, 161)),
                      ContextData(),
                      ObjectType(ObjectIdentity(oid)))
            )
            
            if error_indication:
                logger.error(f"SNMP错误: {error_indication}")
                return None
            elif error_status:
                logger.error(f"SNMP错误: {error_status.prettyPrint()}")
                return None
            else:
                for var_bind in var_binds:
                    return var_bind[1].prettyPrint()
        except Exception as e:
            logger.error(f"SNMP获取数据出错: {str(e)}")
            return None

    @staticmethod
    def get_bandwidth_usage(ip, community):
        """计算带宽使用率"""
        try:
            # 计算带宽使用率需要获取接口的当前流量和接口带宽，然后计算使用率
            # 这里我们先获取第一个接口的信息作为示例
            
            # 获取接口索引
            interface_index = PerformanceCollector.get_first_interface_index(ip, community)
            if not interface_index:
                return None
                
            # 获取接口当前入流量 - ifInOctets
            in_octets_oid = f'1.3.6.1.2.1.2.2.1.10.{interface_index}'
            in_octets = PerformanceCollector.get_snmp_data(ip, community, in_octets_oid)
            
            # 获取接口当前出流量 - ifOutOctets
            out_octets_oid = f'1.3.6.1.2.1.2.2.1.16.{interface_index}'
            out_octets = PerformanceCollector.get_snmp_data(ip, community, out_octets_oid)
            
            # 获取接口带宽 - ifSpeed
            speed_oid = f'1.3.6.1.2.1.2.2.1.5.{interface_index}'
            speed = PerformanceCollector.get_snmp_data(ip, community, speed_oid)
            
            # 如果无法获取完整数据，返回None
            if not in_octets or not out_octets or not speed:
                return None
                
            # 转换为整数
            in_octets = int(in_octets)
            out_octets = int(out_octets)
            speed = int(speed)
            
            # 避免除零错误
            if speed == 0:
                return None
                
            # 简化处理：使用当前流量与接口带宽的比值作为使用率的估计
            # 在实际应用中，应该在两个时间点采样，计算流量变化率
            total_traffic = in_octets + out_octets
            
            # 估算带宽使用率（简化计算，仅作示例）
            usage_percentage = (total_traffic * 8 * 100) / (speed * 60)  # 假设数据是一分钟内的
            
            # 限制在合理范围内
            usage_percentage = min(100, max(0, usage_percentage))
            
            return round(usage_percentage, 1)
        except Exception as e:
            logger.error(f"计算带宽使用率出错: {str(e)}")
            return None
            
    @staticmethod
    def get_first_interface_index(ip, community):
        """获取第一个活动接口的索引"""
        try:
            # 获取接口状态表 - ifOperStatus
            for (error_indication,
                error_status,
                error_index,
                var_binds) in nextCmd(SnmpEngine(),
                                    CommunityData(community),
                                    UdpTransportTarget((ip, 161)),
                                    ContextData(),
                                    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8')),
                                    lexicographicMode=False):
                
                if error_indication or error_status:
                    continue
                    
                for var_bind in var_binds:
                    # 获取OID和值
                    oid = var_bind[0]
                    value = var_bind[1]
                    
                    # 检查接口是否处于活动状态 (1 = up)
                    if value == 1:
                        # 从OID中提取接口索引
                        interface_index = str(oid).split('.')[-1]
                        return interface_index
            
            # 如果没有找到活动接口，返回第一个接口
            return "1"
        except Exception as e:
            logger.error(f"获取接口索引出错: {str(e)}")
            return None
    
    @staticmethod
    def collect_all_devices_performance() -> Dict:
        """
        采集所有设备的性能数据
        
        Returns:
            采集结果字典
        """
        start_time = time.time()
        results = {
            'status': 'success',
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        try:
            # 获取所有设备
            devices = Device.query.filter_by(status='正常').all()
            results['total'] = len(devices)
            
            # 遍历采集每个设备的性能数据
            for device in devices:
                result = PerformanceCollector.collect_device_performance(device.id)
                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1
                results['details'].append(result)
                
            # 记录执行时间
            results['execution_time'] = time.time() - start_time
            return results
            
        except Exception as e:
            logger.error(f"批量采集性能数据出错: {str(e)}")
            results['status'] = 'error'
            results['message'] = f'批量采集性能数据出错: {str(e)}'
            results['execution_time'] = time.time() - start_time
            return results


class ThresholdManager:
    """阈值管理服务"""
    
    @staticmethod
    def check_thresholds(performance_record: PerformanceRecord) -> List[Dict]:
        """
        检查性能数据是否超过阈值
        
        Args:
            performance_record: 性能记录
            
        Returns:
            告警列表
        """
        alerts = []
        
        try:
            # 获取设备的所有阈值设置
            thresholds = Threshold.query.filter_by(device_id=performance_record.device_id).all()
            
            # 检查CPU使用率阈值
            cpu_thresholds = [t for t in thresholds if t.metric_name == 'cpu_usage']
            if cpu_thresholds and performance_record.cpu_usage is not None:
                for threshold in cpu_thresholds:
                    alert = ThresholdManager._check_metric_threshold(
                        'cpu_usage',
                        performance_record.cpu_usage,
                        threshold,
                        performance_record
                    )
                    if alert:
                        alerts.append(alert)
            
            # 检查内存使用率阈值
            memory_thresholds = [t for t in thresholds if t.metric_name == 'memory_usage']
            if memory_thresholds and performance_record.memory_usage is not None:
                for threshold in memory_thresholds:
                    alert = ThresholdManager._check_metric_threshold(
                        'memory_usage',
                        performance_record.memory_usage,
                        threshold,
                        performance_record
                    )
                    if alert:
                        alerts.append(alert)
            
            # 检查带宽使用率阈值
            bandwidth_thresholds = [t for t in thresholds if t.metric_name == 'bandwidth_usage']
            if bandwidth_thresholds and performance_record.bandwidth_usage is not None:
                for threshold in bandwidth_thresholds:
                    alert = ThresholdManager._check_metric_threshold(
                        'bandwidth_usage',
                        performance_record.bandwidth_usage,
                        threshold,
                        performance_record
                    )
                    if alert:
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"检查阈值出错: {str(e)}")
            return []
    
    @staticmethod
    def _check_metric_threshold(
        metric_name: str,
        metric_value: float,
        threshold: Threshold,
        performance_record: PerformanceRecord
    ) -> Optional[Dict]:
        """
        检查指定指标是否超过阈值
        
        Args:
            metric_name: 指标名称
            metric_value: 指标值
            threshold: 阈值设置
            performance_record: 性能记录
            
        Returns:
            告警字典，如果未超过阈值则返回None
        """
        try:
            # 指标显示名称映射
            metric_display_names = {
                'cpu_usage': 'CPU使用率',
                'memory_usage': '内存使用率',
                'bandwidth_usage': '带宽使用率'
            }
            
            # 检查是否超过严重阈值
            if metric_value >= threshold.critical_threshold:
                # 创建告警记录
                alert = ThresholdManager._create_alert(
                    metric_name,
                    metric_value,
                    threshold,
                    'critical',
                    performance_record
                )
                
                # 返回告警信息
                return {
                    'status': 'critical',
                    'metric_name': metric_name,
                    'metric_display_name': metric_display_names.get(metric_name, metric_name),
                    'value': metric_value,
                    'threshold': threshold.critical_threshold,
                    'message': f"{metric_display_names.get(metric_name, metric_name)}超过严重阈值: {metric_value:.1f}% >= {threshold.critical_threshold}%",
                    'alert_id': alert.id if alert else None
                }
                
            # 检查是否超过警告阈值
            elif metric_value >= threshold.warning_threshold:
                # 创建告警记录
                alert = ThresholdManager._create_alert(
                    metric_name,
                    metric_value,
                    threshold,
                    'warning',
                    performance_record
                )
                
                # 返回告警信息
                return {
                    'status': 'warning',
                    'metric_name': metric_name,
                    'metric_display_name': metric_display_names.get(metric_name, metric_name),
                    'value': metric_value,
                    'threshold': threshold.warning_threshold,
                    'message': f"{metric_display_names.get(metric_name, metric_name)}超过警告阈值: {metric_value:.1f}% >= {threshold.warning_threshold}%",
                    'alert_id': alert.id if alert else None
                }
                
            return None
            
        except Exception as e:
            logger.error(f"检查指标阈值出错: {str(e)}")
            return None
    
    @staticmethod
    def _create_alert(
        metric_name: str,
        metric_value: float,
        threshold: Threshold,
        severity: str,
        performance_record: PerformanceRecord
    ) -> Optional[Alert]:
        """
        创建告警记录
        
        Args:
            metric_name: 指标名称
            metric_value: 指标值
            threshold: 阈值设置
            severity: 严重程度
            performance_record: 性能记录
            
        Returns:
            创建的告警记录，如果创建失败则返回None
        """
        try:
            # 指标显示名称映射
            metric_display_names = {
                'cpu_usage': 'CPU使用率',
                'memory_usage': '内存使用率',
                'bandwidth_usage': '带宽使用率'
            }
            
            # 构建告警消息
            if severity == 'critical':
                message = f"{metric_display_names.get(metric_name, metric_name)}超过严重阈值: {metric_value:.1f}% >= {threshold.critical_threshold}%"
                threshold_value = threshold.critical_threshold
            else:
                message = f"{metric_display_names.get(metric_name, metric_name)}超过警告阈值: {metric_value:.1f}% >= {threshold.warning_threshold}%"
                threshold_value = threshold.warning_threshold
                
            # 创建告警类型标识
            alert_type = f'PERFORMANCE_{metric_name.upper()}'
            
            # 检查是否已存在相同类型的活跃告警
            device = Device.query.get(performance_record.device_id)
            from src.core.models import Fault  # 避免循环导入
            
            # 查找是否有相关故障
            fault = Fault.query.filter_by(
                device_id=performance_record.device_id,
                fault_type=alert_type,
                status='open'
            ).first()
            
            # 如果没有相关故障，创建一个
            if not fault:
                fault = Fault(
                    device_id=performance_record.device_id,
                    fault_type=alert_type,
                    severity=severity,
                    description=f"{device.name} - {message}",
                    status='open'
                )
                db.session.add(fault)
                db.session.flush()  # 获取故障ID
            
            # 创建告警记录
            alert = Alert(
                fault_id=fault.id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                status='active'
            )
            
            db.session.add(alert)
            db.session.commit()
            
            return alert
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建告警出错: {str(e)}")
            return None


class PerformanceAnalyzer:
    """性能分析服务"""
    
    @staticmethod
    def analyze_device_performance(device_id: int, days: int = 7) -> Dict:
        """
        分析设备性能趋势
        
        Args:
            device_id: 设备ID
            days: 分析天数
            
        Returns:
            分析结果字典
        """
        try:
            # 获取设备信息
            device = Device.query.get(device_id)
            if not device:
                return {'status': 'error', 'message': f'设备不存在: {device_id}'}
            
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 查询性能记录
            records = PerformanceRecord.query.filter(
                PerformanceRecord.device_id == device_id,
                PerformanceRecord.recorded_at >= start_time,
                PerformanceRecord.recorded_at <= end_time
            ).order_by(PerformanceRecord.recorded_at).all()
            
            if not records:
                return {
                    'status': 'warning',
                    'message': f'没有找到设备"{device.name}"在过去{days}天的性能记录'
                }
            
            # 计算各项指标的平均值、最大值、最小值
            cpu_values = [r.cpu_usage for r in records if r.cpu_usage is not None]
            memory_values = [r.memory_usage for r in records if r.memory_usage is not None]
            bandwidth_values = [r.bandwidth_usage for r in records if r.bandwidth_usage is not None]
            
            # 计算CPU使用率统计
            cpu_stats = PerformanceAnalyzer._calculate_stats(cpu_values)
            
            # 计算内存使用率统计
            memory_stats = PerformanceAnalyzer._calculate_stats(memory_values)
            
            # 计算带宽使用率统计
            bandwidth_stats = PerformanceAnalyzer._calculate_stats(bandwidth_values)
            
            # 返回分析结果
            return {
                'status': 'success',
                'device_id': device_id,
                'device_name': device.name,
                'analysis_period': {
                    'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'days': days
                },
                'sample_count': len(records),
                'cpu_usage': cpu_stats,
                'memory_usage': memory_stats,
                'bandwidth_usage': bandwidth_stats
            }
            
        except Exception as e:
            logger.error(f"分析设备性能出错: {str(e)}")
            return {'status': 'error', 'message': f'分析设备性能出错: {str(e)}'}
    
    @staticmethod
    def _calculate_stats(values: List[float]) -> Dict:
        """
        计算数值列表的统计信息
        
        Args:
            values: 数值列表
            
        Returns:
            统计信息字典
        """
        if not values:
            return {
                'avg': None,
                'max': None,
                'min': None,
                'samples': 0
            }
        
        return {
            'avg': sum(values) / len(values),
            'max': max(values),
            'min': min(values),
            'samples': len(values)
        } 