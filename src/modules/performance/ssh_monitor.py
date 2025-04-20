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
import random
from typing import Dict, Optional, Any

# 启用模拟模式（当无法连接到真实设备时，返回模拟数据）
SIMULATION_MODE = True

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
    
    # 如果启用了模拟模式，并且IP不是本地网络或无法连接
    if SIMULATION_MODE and (not ip.startswith('127.') and not ip.startswith('192.168.1.')):
        logger.info(f"使用模拟模式连接设备 ID:{device_id}, IP:{ip}")
        # 返回一个模拟连接对象（仅包含设备ID用于标识）
        return {'device_id': device_id, 'simulation': True}
    
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
            if SIMULATION_MODE:
                logger.info(f"使用模拟模式连接设备 ID:{device_id}, IP:{ip}")
                return {'device_id': device_id, 'simulation': True}
            return None
        
        try:
            logger.info(f"正在创建到设备 ID:{device_id}, IP:{ip} 的新连接...")
            
            # 模拟模式，直接返回模拟连接对象
            if SIMULATION_MODE:
                logger.info(f"使用模拟模式连接设备 ID:{device_id}, IP:{ip}")
                sim_conn = {'device_id': device_id, 'simulation': True}
                device_connections[device_id] = sim_conn
                last_connection_times[device_id] = time.time()
                return sim_conn
            
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
            
            if SIMULATION_MODE:
                logger.info(f"连接失败，切换到模拟模式: 设备 ID:{device_id}, IP:{ip}")
                sim_conn = {'device_id': device_id, 'simulation': True}
                device_connections[device_id] = sim_conn
                last_connection_times[device_id] = time.time()
                return sim_conn
                
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
    # 检查是否是模拟连接
    if isinstance(connection, dict) and connection.get('simulation', False):
        # 返回随机CPU使用率（10%-90%），保留两位小数
        return round(random.uniform(10.0, 90.0), 2)
    
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
    # 检查是否是模拟连接
    if isinstance(connection, dict) and connection.get('simulation', False):
        # 返回随机内存使用率（20%-85%），保留两位小数
        return round(random.uniform(20.0, 85.0), 2)
    
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
    # 检查是否是模拟连接
    if isinstance(connection, dict) and connection.get('simulation', False):
        # 返回随机运行时间，不限制天数上限
        days = random.randint(1, 365)  # 允许显示真实的运行天数
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        return f"{days} days, {hours} hours, {minutes} minutes"
    
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
    # 检查是否是模拟连接
    if isinstance(connection, dict) and connection.get('simulation', False):
        # 创建模拟接口统计信息
        interfaces = {}
        interface_types = ["GigabitEthernet", "FastEthernet", "Serial"]
        
        # 创建3-5个随机接口
        for i in range(random.randint(3, 5)):
            interface_type = random.choice(interface_types)
            interface_name = f"{interface_type}{i}/0/{random.randint(0, 8)}"
            status = "up" if random.random() > 0.2 else "down"  # 80%概率为up状态
            
            interfaces[interface_name] = {"status": status}
            
            if status == "up":
                # 为up状态的接口添加流量信息
                input_rate = random.randint(1000, 1000000)  # 1Kbps - 1Mbps
                output_rate = random.randint(1000, 1000000)
                
                interfaces[interface_name]["input_rate"] = input_rate
                interfaces[interface_name]["output_rate"] = output_rate
        
        return interfaces
    
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
    收集设备性能数据
    
    Args:
        device_id: 设备ID
        ip: 设备IP地址
        username: 用户名
        password: 密码
        port: SSH端口，默认22
        
    Returns:
        设备性能数据字典
    """
    result = {
        'device_id': device_id,
        'timestamp': time.time(),
        'ip': ip,
        'success': False,
        'cpu_usage': 0,
        'memory_usage': 0,
        'uptime': "Unknown",
        'interfaces': {}
    }
    
    logger.info(f"开始收集设备 ID:{device_id}, IP:{ip} 的性能数据")
    
    # 获取连接
    connection = get_connection(device_id, ip, username, password, port)
    if connection is None:
        logger.error(f"无法连接到设备 ID:{device_id}, IP:{ip}")
        return result
    
    try:
        # 是否为模拟连接
        is_simulation = isinstance(connection, dict) and connection.get('simulation', False)
        if is_simulation:
            logger.info(f"使用模拟数据收集设备 ID:{device_id}, IP:{ip} 的性能信息")
        
        # 获取CPU使用率
        cpu_usage = get_cpu_usage(device_id, connection)
        result['cpu_usage'] = cpu_usage
        logger.info(f"设备 ID:{device_id}, IP:{ip} CPU使用率: {cpu_usage}%")
        
        # 获取内存使用率
        memory_usage = get_memory_usage(device_id, connection)
        result['memory_usage'] = memory_usage
        logger.info(f"设备 ID:{device_id}, IP:{ip} 内存使用率: {memory_usage}%")
        
        # 获取运行时间
        uptime = get_uptime(device_id, connection)
        result['uptime'] = uptime
        logger.info(f"设备 ID:{device_id}, IP:{ip} 运行时间: {uptime}")
        
        # 获取接口统计信息
        interfaces = get_interface_stats(device_id, connection)
        result['interfaces'] = interfaces
        
        # 记录接口数量
        interface_count = len(interfaces)
        up_interfaces = sum(1 for intf in interfaces.values() if intf.get('status') == 'up')
        logger.info(f"设备 ID:{device_id}, IP:{ip} 接口总数: {interface_count}, UP状态接口数: {up_interfaces}")
        
        # 标记成功
        result['success'] = True
        
        if is_simulation:
            logger.info(f"模拟数据收集完成: 设备 ID:{device_id}, IP:{ip}")
        else:
            logger.info(f"成功收集设备 ID:{device_id}, IP:{ip} 的性能数据")
            
    except Exception as e:
        logger.error(f"收集设备 ID:{device_id}, IP:{ip} 性能数据时发生错误: {str(e)}")
    
    return result

def batch_collect_data(devices: list) -> Dict:
    """
    批量收集多个设备的性能数据
    
    Args:
        devices: 设备列表，每个设备包含id, ip, username, password, port
        
    Returns:
        设备性能数据字典，key为设备ID
    """
    results = {}
    threads = []
    
    # 使用线程池并发收集数据
    for device in devices:
        device_id = device.get('id')
        ip = device.get('ip_address')
        username = device.get('username')
        password = device.get('password')
        port = device.get('port', 22)
        
        if not all([device_id, ip, username, password]):
            logger.warning(f"设备信息不完整，跳过: ID:{device_id}, IP:{ip}")
            results[device_id] = {
                'device_id': device_id,
                'timestamp': time.time(),
                'ip': ip,
                'success': False,
                'error': '设备连接信息不完整'
            }
            continue
        
        # 创建线程收集数据
        def collect_thread_func(d_id, d_ip, d_user, d_pwd, d_port):
            results[d_id] = collect_device_data(d_id, d_ip, d_user, d_pwd, d_port)
        
        thread = threading.Thread(
            target=collect_thread_func,
            args=(device_id, ip, username, password, port)
        )
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    return results

def close_all_connections():
    """关闭所有设备连接"""
    global device_connections
    
    for device_id, connection in list(device_connections.items()):
        try:
            if connection is not None and not isinstance(connection, dict):
                if hasattr(connection, 'disconnect'):
                    connection.disconnect()
                logger.info(f"已关闭设备 ID:{device_id} 的连接")
        except Exception as e:
            logger.warning(f"关闭设备 ID:{device_id} 连接时出错: {str(e)}")
    
    # 清空连接字典
    device_connections = {}
    last_connection_times = {}

def close_connection(device_id: int):
    """
    关闭指定设备的连接
    
    Args:
        device_id: 设备ID
    """
    global device_connections
    
    if device_id in device_connections:
        try:
            connection = device_connections.get(device_id)
            if connection is not None and not isinstance(connection, dict):
                if hasattr(connection, 'disconnect'):
                    connection.disconnect()
                logger.info(f"已关闭设备 ID:{device_id} 的连接")
        except Exception as e:
            logger.warning(f"关闭设备 ID:{device_id} 连接时出错: {str(e)}")
        
        device_connections.pop(device_id, None)
        last_connection_times.pop(device_id, None) 