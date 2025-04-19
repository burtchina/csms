#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSH连接监控模块，用于连接网络设备并获取性能数据
"""

import time
import re
import threading
import logging
import paramiko
from typing import Dict, Optional, Any

try:
    from netmiko import ConnectHandler
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    logging.warning("Netmiko未安装，设备连接功能将不可用")

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 连接锁，防止多线程同时操作连接
connection_locks = {}  # 格式: {device_id: threading.Lock()}
# 当前连接对象
device_connections = {}  # 格式: {device_id: connection_object}
# 上次连接时间
last_connection_times = {}  # 格式: {device_id: timestamp}

def get_connection(device_id: int, ip: str, username: str, password: str, port: int = 22) -> Optional[Any]:
    """
    获取或创建到设备的SSH连接
    
    Args:
        device_id: 设备ID
        ip: 设备IP地址
        username: 用户名
        password: 密码
        port: SSH端口，默认22
        
    Returns:
        SSH连接对象，如果连接失败则返回None
    """
    global device_connections, last_connection_times
    
    # 确保该设备有连接锁
    if device_id not in connection_locks:
        connection_locks[device_id] = threading.Lock()
    
    with connection_locks[device_id]:
        # 检查连接是否存在且有效
        if device_id in device_connections and device_connections[device_id] is not None:
            try:
                # 发送简单命令测试连接是否有效
                if hasattr(device_connections[device_id], 'find_prompt'):
                    device_connections[device_id].find_prompt()
                return device_connections[device_id]
            except Exception as e:
                logger.warning(f"设备 {device_id} 的连接已失效，准备重新连接: {str(e)}")
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
            logger.info(f"正在创建到设备 ID:{device_id}, IP:{ip} 的新连接...")
            
            # 设置连接参数
            device_info = {
                'device_type': 'huawei',  # 默认使用华为设备
                'ip': ip,
                'username': username,
                'password': password,
                'port': port,
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
            logger.info(f"成功建立到设备 ID:{device_id}, IP:{ip} 的新连接")
            
            # 发送keep-alive配置命令（如果设备支持）
            try:
                conn.send_command("screen-length 0 temporary")  # 禁用分页
            except Exception as e:
                logger.warning(f"设置分页失败: {str(e)}")
                
            return conn
        except Exception as e:
            logger.error(f"创建设备 ID:{device_id}, IP:{ip} 的连接失败: {str(e)}")
            return None

def get_cpu_usage(device_id: int, connection: Any) -> float:
    """
    获取CPU使用率
    
    Args:
        device_id: 设备ID
        connection: SSH连接对象
        
    Returns:
        CPU使用率百分比，失败时返回0
    """
    try:
        output = connection.send_command('display cpu-usage')
        match = re.search(r'CPU Usage\s+:\s+(\d+)%', output)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        logger.error(f"获取设备 {device_id} CPU使用率失败: {str(e)}")
        return 0.0

def get_memory_usage(device_id: int, connection: Any) -> float:
    """
    获取内存使用率
    
    Args:
        device_id: 设备ID
        connection: SSH连接对象
        
    Returns:
        内存使用率百分比，失败时返回0
    """
    try:
        output = connection.send_command('display memory-usage')
        match = re.search(r'Memory utilization\s+:\s+(\d+)%', output)
        if match:
            return float(match.group(1))
        return 0.0
    except Exception as e:
        logger.error(f"获取设备 {device_id} 内存使用率失败: {str(e)}")
        return 0.0

def get_uptime(device_id: int, connection: Any) -> str:
    """
    获取设备运行时间
    
    Args:
        device_id: 设备ID
        connection: SSH连接对象
        
    Returns:
        运行时间字符串，失败时返回"Unknown"
    """
    try:
        output = connection.send_command('display version')
        match = re.search(r'Uptime is\s+(.+)', output)
        if match:
            return match.group(1)
        return "Unknown"
    except Exception as e:
        logger.error(f"获取设备 {device_id} 运行时间失败: {str(e)}")
        return "Unknown"

def get_interface_stats(device_id: int, connection: Any) -> Dict:
    """
    获取接口统计信息
    
    Args:
        device_id: 设备ID
        connection: SSH连接对象
        
    Returns:
        接口统计信息字典
    """
    interfaces = {}
    
    try:
        # 1. 获取接口列表
        output = connection.send_command('display interface brief')
        
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
                output = connection.send_command(f'display interface {interface}')
                
                # 提取输入/输出速率
                input_match = re.search(r'input.+?(\d+)\s+bits/sec', output, re.DOTALL)
                output_match = re.search(r'output.+?(\d+)\s+bits/sec', output, re.DOTALL)
                
                input_rate = int(input_match.group(1)) if input_match else 0
                output_rate = int(output_match.group(1)) if output_match else 0
                
                interfaces[interface]["input_rate"] = input_rate
                interfaces[interface]["output_rate"] = output_rate
            except Exception as e:
                logger.error(f"获取设备 {device_id} 接口 {interface} 信息时出错: {str(e)}")
    except Exception as e:
        logger.error(f"获取设备 {device_id} 接口统计信息失败: {str(e)}")
    
    return interfaces

def collect_device_data(device_id: int, ip: str, username: str, password: str, port: int = 22) -> Dict:
    """
    从设备收集性能数据
    
    Args:
        device_id: 设备ID
        ip: 设备IP地址
        username: 用户名
        password: 密码
        port: SSH端口，默认22
        
    Returns:
        性能数据字典
    """
    try:
        # 获取SSH连接
        connection = get_connection(device_id, ip, username, password, port)
        if not connection:
            logger.error(f"无法连接到设备 ID:{device_id}, IP:{ip}")
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'uptime': '连接失败',
                'timestamp': time.time(),
                'error': '无法建立SSH连接'
            }
        
        # 获取性能数据
        cpu_usage = get_cpu_usage(device_id, connection)
        memory_usage = get_memory_usage(device_id, connection)
        uptime = get_uptime(device_id, connection)
        interfaces = get_interface_stats(device_id, connection)
        
        # 返回结果
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'uptime': uptime,
            'interfaces': interfaces,
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"从设备 ID:{device_id}, IP:{ip} 收集数据时出错: {str(e)}")
        return {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'uptime': '数据收集出错',
            'timestamp': time.time(),
            'error': str(e)
        }

def close_connection(device_id: int) -> bool:
    """
    关闭到设备的SSH连接
    
    Args:
        device_id: 设备ID
        
    Returns:
        是否成功关闭连接
    """
    if device_id in device_connections and device_connections[device_id] is not None:
        with connection_locks.get(device_id, threading.Lock()):
            try:
                device_connections[device_id].disconnect()
                device_connections[device_id] = None
                logger.info(f"已关闭设备 {device_id} 的连接")
                return True
            except Exception as e:
                logger.error(f"关闭设备 {device_id} 连接时出错: {str(e)}")
    return False

def close_all_connections() -> None:
    """关闭所有SSH连接"""
    for device_id in list(device_connections.keys()):
        close_connection(device_id) 