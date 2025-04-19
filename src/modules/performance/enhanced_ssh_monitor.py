#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强版SSH连接监控模块，用于连接网络设备并获取性能数据
支持多种设备类型，提供更全面的连接管理和数据采集功能
"""

import time
import re
import threading
import logging
import paramiko
from typing import Dict, Optional, Any, List, Tuple, Union

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import NetMikoTimeoutException, NetMikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    logging.warning("Netmiko未安装，设备连接功能将不可用")

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局连接管理
connection_locks = {}  # 格式: {device_id: threading.Lock()}
device_connections = {}  # 格式: {device_id: connection_object}
last_connection_times = {}  # 格式: {device_id: timestamp}
connection_status = {}  # 格式: {device_id: {"status": "connected", "last_error": "", "reconnect_attempts": 0}}

# 设备厂商映射
VENDOR_MAP = {
    "huawei": {
        "device_type": "huawei",
        "disable_paging_cmd": "screen-length 0 temporary",
        "cpu_cmd": "display cpu-usage",
        "memory_cmd": "display memory-usage",
        "version_cmd": "display version",
        "interface_cmd": "display interface brief",
        "interface_detail_cmd": "display interface {interface}",
        # 正则表达式模式
        "cpu_pattern": r'CPU Usage\s*:\s*(\d+(\.\d+)?)%',
        "memory_pattern": r'Memory utilization\s*:\s*(\d+(\.\d+)?)%',
        "uptime_pattern": r'[Uu]ptime is\s+(.+)',
        "interface_input_pattern": r'input.+?(\d+)\s+bits/sec',
        "interface_output_pattern": r'output.+?(\d+)\s+bits/sec',
    },
    "cisco": {
        "device_type": "cisco_ios",
        "disable_paging_cmd": "terminal length 0",
        "cpu_cmd": "show processes cpu | include CPU utilization",
        "memory_cmd": "show memory statistics | include Processor",
        "version_cmd": "show version | include uptime",
        "interface_cmd": "show ip interface brief",
        "interface_detail_cmd": "show interface {interface}",
        # 正则表达式模式
        "cpu_pattern": r'CPU utilization.+?(\d+)%',
        "memory_pattern": r'Processor\s+(\d+)',
        "uptime_pattern": r'uptime is\s+(.+)',
        "interface_input_pattern": r'input rate\s+(\d+)\s+bits/sec',
        "interface_output_pattern": r'output rate\s+(\d+)\s+bits/sec',
    },
    # 可以添加更多厂商的支持
}

def detect_device_vendor(connection: Any) -> str:
    """
    检测设备厂商类型
    
    Args:
        connection: SSH连接对象
        
    Returns:
        设备厂商类型字符串，如 "huawei", "cisco" 等
    """
    try:
        # 尝试获取系统信息
        output = connection.send_command("display version")
        if "huawei" in output.lower():
            return "huawei"
        
        output = connection.send_command("show version")
        if "cisco" in output.lower():
            return "cisco"
        
        # 默认返回huawei
        return "huawei"
    except Exception as e:
        logger.warning(f"无法检测设备厂商类型: {str(e)}")
        return "huawei"  # 默认使用华为设备

def get_connection(device_id: int, ip: str, username: str, password: str, 
                  port: int = 22, vendor: str = "huawei", 
                  timeout: int = 10) -> Optional[Any]:
    """
    获取或创建到设备的SSH连接
    
    Args:
        device_id: 设备ID
        ip: 设备IP地址
        username: 用户名
        password: 密码
        port: SSH端口，默认22
        vendor: 设备厂商，默认'huawei'
        timeout: 连接超时时间，默认10秒
        
    Returns:
        SSH连接对象，如果连接失败则返回None
    """
    global device_connections, last_connection_times, connection_status
    
    # 确保该设备有连接锁
    if device_id not in connection_locks:
        connection_locks[device_id] = threading.Lock()
    
    with connection_locks[device_id]:
        # 初始化连接状态
        if device_id not in connection_status:
            connection_status[device_id] = {
                "status": "disconnected",
                "last_error": "",
                "reconnect_attempts": 0,
                "vendor": vendor
            }
            
        # 检查连接是否存在且有效
        if device_id in device_connections and device_connections[device_id] is not None:
            try:
                # 发送简单命令测试连接是否有效
                if hasattr(device_connections[device_id], 'find_prompt'):
                    device_connections[device_id].find_prompt()
                
                connection_status[device_id]["status"] = "connected"
                connection_status[device_id]["reconnect_attempts"] = 0
                return device_connections[device_id]
            except Exception as e:
                logger.warning(f"设备 {device_id} 的连接已失效，准备重新连接: {str(e)}")
                try:
                    device_connections[device_id].disconnect()
                except:
                    pass
                device_connections[device_id] = None
                connection_status[device_id]["status"] = "reconnecting"
                connection_status[device_id]["last_error"] = str(e)
        
        # 连接不存在或无效，创建新连接
        # 检查是否频繁重连（防止在短时间内多次重连）
        current_time = time.time()
        if device_id in last_connection_times and current_time - last_connection_times.get(device_id, 0) < 5:
            time.sleep(2)  # 等待一段时间再重连
        
        # 检查是否有netmiko支持
        if not NETMIKO_AVAILABLE:
            logger.warning("Netmiko未安装，无法连接设备")
            connection_status[device_id]["status"] = "error"
            connection_status[device_id]["last_error"] = "Netmiko未安装"
            return None
        
        try:
            logger.info(f"正在创建到设备 ID:{device_id}, IP:{ip} 的新连接...")
            
            # 增加重连尝试计数
            if connection_status[device_id]["status"] == "reconnecting":
                connection_status[device_id]["reconnect_attempts"] += 1
            
            # 设置连接参数
            vendor_type = vendor.lower() if vendor else "huawei"
            if vendor_type not in VENDOR_MAP:
                vendor_type = "huawei"  # 默认使用华为设备
                
            device_info = {
                'device_type': VENDOR_MAP[vendor_type]["device_type"],
                'ip': ip,
                'username': username,
                'password': password,
                'port': port,
                'timeout': timeout,
                'session_timeout': 60,
                'keepalive': 30,
                'global_delay_factor': 2,
                'fast_cli': False,  # 禁用快速CLI，增加兼容性
            }
            
            # 使用ConnectHandler连接设备
            conn = ConnectHandler(**device_info)
            
            # 发送一个简单命令确认连接正常
            conn.find_prompt()
            
            # 尝试自动检测设备类型
            detected_vendor = detect_device_vendor(conn)
            connection_status[device_id]["vendor"] = detected_vendor
            
            # 存储连接
            device_connections[device_id] = conn
            last_connection_times[device_id] = time.time()
            
            # 更新状态
            connection_status[device_id]["status"] = "connected"
            connection_status[device_id]["reconnect_attempts"] = 0
            connection_status[device_id]["last_error"] = ""
            
            logger.info(f"成功建立到设备 ID:{device_id}, IP:{ip} 的新连接")
            
            # 发送禁用分页命令
            try:
                disable_paging_cmd = VENDOR_MAP[detected_vendor]["disable_paging_cmd"]
                conn.send_command(disable_paging_cmd)
                logger.debug(f"已发送禁用分页命令: {disable_paging_cmd}")
            except Exception as e:
                logger.warning(f"设置分页失败: {str(e)}")
                
            return conn
            
        except NetMikoTimeoutException:
            error_msg = f"连接超时: 设备 {ip} 可能无法访问或SSH服务未启用"
            logger.error(error_msg)
            connection_status[device_id]["status"] = "timeout"
            connection_status[device_id]["last_error"] = error_msg
            return None
            
        except NetMikoAuthenticationException:
            error_msg = f"认证失败: 用户名或密码错误"
            logger.error(error_msg)
            connection_status[device_id]["status"] = "auth_failed"
            connection_status[device_id]["last_error"] = error_msg
            return None
            
        except Exception as e:
            error_msg = f"创建设备 ID:{device_id}, IP:{ip} 的连接失败: {str(e)}"
            logger.error(error_msg)
            connection_status[device_id]["status"] = "error"
            connection_status[device_id]["last_error"] = error_msg
            return None

def get_device_status(device_id: int) -> Dict:
    """
    获取设备连接状态
    
    Args:
        device_id: 设备ID
        
    Returns:
        设备连接状态信息
    """
    if device_id not in connection_status:
        return {
            "status": "unknown",
            "last_error": "",
            "reconnect_attempts": 0,
            "connected": False,
            "vendor": "unknown"
        }
    
    status = connection_status[device_id].copy()
    status["connected"] = status["status"] == "connected"
    return status

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
        vendor = connection_status.get(device_id, {}).get("vendor", "huawei")
        cmd = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["cpu_cmd"]
        pattern = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["cpu_pattern"]
        
        logger.debug(f"执行CPU命令: {cmd}")
        output = connection.send_command(cmd)
        logger.debug(f"CPU命令输出: {output}")
        
        match = re.search(pattern, output)
        if match:
            return float(match.group(1))
        
        # 尝试备用正则表达式
        fallback_patterns = [
            r'CPU.+?(\d+(\.\d+)?)%',  # 通用模式
            r'(\d+(\.\d+)?)%\s+CPU',
            r'utilization\s*:\s*(\d+(\.\d+)?)%'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, output)
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
        vendor = connection_status.get(device_id, {}).get("vendor", "huawei")
        cmd = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["memory_cmd"]
        pattern = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["memory_pattern"]
        
        logger.debug(f"执行内存命令: {cmd}")
        output = connection.send_command(cmd)
        logger.debug(f"内存命令输出: {output}")
        
        match = re.search(pattern, output)
        if match:
            return float(match.group(1))
        
        # 尝试备用正则表达式
        fallback_patterns = [
            r'Memory.+?(\d+(\.\d+)?)%',  # 通用模式
            r'memory utilization\s*:\s*(\d+(\.\d+)?)%',
            r'Memory usage\s*:\s*(\d+(\.\d+)?)%'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, output)
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
        vendor = connection_status.get(device_id, {}).get("vendor", "huawei")
        cmd = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["version_cmd"]
        pattern = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["uptime_pattern"]
        
        logger.debug(f"执行版本命令: {cmd}")
        output = connection.send_command(cmd)
        logger.debug(f"版本命令输出: {output}")
        
        match = re.search(pattern, output)
        if match:
            return match.group(1)
        
        # 尝试备用正则表达式
        fallback_patterns = [
            r'[Uu]ptime\s+(?:is|:)\s+(.+)',
            r'[Ss]ystem uptime\s*:\s*(.+)',
            r'has been up for\s+(.+)'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
                
        return "Unknown"
    except Exception as e:
        logger.error(f"获取设备 {device_id} 运行时间失败: {str(e)}")
        return "Unknown"

def get_interface_stats(device_id: int, connection: Any, max_interfaces: int = 5) -> Dict:
    """
    获取接口统计信息
    
    Args:
        device_id: 设备ID
        connection: SSH连接对象
        max_interfaces: 最大收集接口数，默认5个
        
    Returns:
        接口统计信息字典
    """
    interfaces = {}
    
    try:
        vendor = connection_status.get(device_id, {}).get("vendor", "huawei")
        interface_cmd = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["interface_cmd"]
        interface_detail_cmd = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["interface_detail_cmd"]
        input_pattern = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["interface_input_pattern"]
        output_pattern = VENDOR_MAP.get(vendor, VENDOR_MAP["huawei"])["interface_output_pattern"]
        
        # 1. 获取接口列表
        logger.debug(f"执行接口列表命令: {interface_cmd}")
        output = connection.send_command(interface_cmd)
        
        # 解析接口信息 - 不同设备厂商有不同的输出格式
        if vendor == "huawei":
            # 华为设备接口解析
            for line in output.splitlines():
                # 匹配常见的接口类型
                if any(intf_type in line for intf_type in ['GigabitEthernet', 'Ethernet', 'Vlanif', 'LoopBack']):
                    parts = line.split()
                    if len(parts) >= 2:
                        interface_name = parts[0]
                        status = "up" if "up" in line.lower() and "down" not in line.lower() else "down"
                        interfaces[interface_name] = {
                            "status": status,
                            "type": interface_name.split('GigabitEthernet')[0] if 'GigabitEthernet' in interface_name else "Unknown"
                        }
        elif vendor == "cisco":
            # 思科设备接口解析
            for line in output.splitlines():
                if "unassigned" in line or "." in line.split()[0]:  # 有IP地址的接口或子接口
                    parts = line.split()
                    if len(parts) >= 5:
                        interface_name = parts[0]
                        status = "up" if parts[4].lower() == "up" else "down"
                        interfaces[interface_name] = {
                            "status": status,
                            "type": interface_name.split('/')[0] if '/' in interface_name else "Unknown"
                        }
        else:
            # 通用解析方法
            for line in output.splitlines():
                # 匹配任何看起来像接口名的内容
                match = re.search(r'([A-Za-z0-9\/\.-]+)\s+', line)
                if match:
                    interface_name = match.group(1)
                    status = "up" if "up" in line.lower() and "down" not in line.lower() else "down"
                    interfaces[interface_name] = {
                        "status": status,
                        "type": interface_name.split('/')[0] if '/' in interface_name else "Unknown"
                    }
        
        # 2. 仅获取UP状态接口的流量信息（最多max_interfaces个）
        up_interfaces = [intf for intf, data in interfaces.items() if data['status'] == 'up']
        for interface in up_interfaces[:max_interfaces]:
            try:
                cmd = interface_detail_cmd.format(interface=interface)
                logger.debug(f"执行接口详情命令: {cmd}")
                output = connection.send_command(cmd)
                
                # 提取输入/输出速率
                input_match = re.search(input_pattern, output, re.DOTALL)
                output_match = re.search(output_pattern, output, re.DOTALL)
                
                input_rate = int(input_match.group(1)) if input_match else 0
                output_rate = int(output_match.group(1)) if output_match else 0
                
                # 将bps转换为更易读的单位
                interfaces[interface]["input_rate"] = input_rate
                interfaces[interface]["output_rate"] = output_rate
                interfaces[interface]["input_rate_formatted"] = format_bandwidth(input_rate)
                interfaces[interface]["output_rate_formatted"] = format_bandwidth(output_rate)
                
                # 提取更多接口信息
                mac_match = re.search(r'MAC\s+[Aa]ddress[^\w]*:\s*([0-9a-fA-F\-:]+)', output)
                if mac_match:
                    interfaces[interface]["mac_address"] = mac_match.group(1)
                
                # 提取错误和丢包信息
                errors_in_match = re.search(r'input\s+error[s]*\s+(\d+)', output, re.IGNORECASE)
                errors_out_match = re.search(r'output\s+error[s]*\s+(\d+)', output, re.IGNORECASE)
                
                if errors_in_match:
                    interfaces[interface]["input_errors"] = int(errors_in_match.group(1))
                if errors_out_match:
                    interfaces[interface]["output_errors"] = int(errors_out_match.group(1))
                
            except Exception as e:
                logger.error(f"获取设备 {device_id} 接口 {interface} 信息时出错: {str(e)}")
    except Exception as e:
        logger.error(f"获取设备 {device_id} 接口统计信息失败: {str(e)}")
    
    return interfaces

def format_bandwidth(bits_per_sec: int) -> str:
    """
    将比特率格式化为易读的带宽表示
    
    Args:
        bits_per_sec: 比特每秒
        
    Returns:
        格式化后的带宽字符串
    """
    if bits_per_sec < 1000:
        return f"{bits_per_sec} bps"
    elif bits_per_sec < 1000000:
        return f"{bits_per_sec/1000:.2f} Kbps"
    elif bits_per_sec < 1000000000:
        return f"{bits_per_sec/1000000:.2f} Mbps"
    else:
        return f"{bits_per_sec/1000000000:.2f} Gbps"

def collect_device_data(device_id: int, ip: str, username: str, password: str, 
                       port: int = 22, vendor: str = "huawei") -> Dict:
    """
    从设备收集综合性能数据
    
    Args:
        device_id: 设备ID
        ip: 设备IP地址
        username: 用户名
        password: 密码
        port: SSH端口，默认22
        vendor: 设备厂商，默认'huawei'
        
    Returns:
        性能数据字典
    """
    try:
        # 获取SSH连接
        connection = get_connection(device_id, ip, username, password, port, vendor)
        if not connection:
            return {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'uptime': '连接失败',
                'timestamp': time.time(),
                'error': '无法建立SSH连接',
                'connection_status': get_device_status(device_id)
            }
        
        # 获取性能数据
        cpu_usage = get_cpu_usage(device_id, connection)
        memory_usage = get_memory_usage(device_id, connection)
        uptime = get_uptime(device_id, connection)
        interfaces = get_interface_stats(device_id, connection)
        
        # 计算总带宽使用率 (仅作为示例，实际可能需要更复杂的计算)
        total_input = 0
        total_output = 0
        for intf, data in interfaces.items():
            if 'input_rate' in data:
                total_input += data['input_rate']
            if 'output_rate' in data:
                total_output += data['output_rate']
        
        # 计算带宽利用率百分比 (假设链路总容量为1Gbps)
        # 这只是一个示例，实际应用中应该根据接口实际速率计算
        link_capacity = 1000000000  # 1Gbps in bps
        total_interfaces = len([i for i in interfaces.values() if i.get('status') == 'up'])
        if total_interfaces > 0:
            bandwidth_usage = max(
                (total_input / (link_capacity * total_interfaces)) * 100,
                (total_output / (link_capacity * total_interfaces)) * 100
            )
        else:
            bandwidth_usage = 0.0
            
        # 限制带宽使用率的最大值为100%
        bandwidth_usage = min(bandwidth_usage, 100.0)
        
        # 返回结果
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'uptime': uptime,
            'interfaces': interfaces,
            'bandwidth_usage': round(bandwidth_usage, 2),
            'total_input_rate': format_bandwidth(total_input),
            'total_output_rate': format_bandwidth(total_output),
            'timestamp': time.time(),
            'connection_status': get_device_status(device_id)
        }
    except Exception as e:
        logger.error(f"从设备 ID:{device_id}, IP:{ip} 收集数据时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'uptime': '数据收集出错',
            'timestamp': time.time(),
            'error': str(e),
            'connection_status': get_device_status(device_id)
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
                
                # 更新连接状态
                if device_id in connection_status:
                    connection_status[device_id]["status"] = "disconnected"
                    
                logger.info(f"已关闭设备 {device_id} 的连接")
                return True
            except Exception as e:
                logger.error(f"关闭设备 {device_id} 连接时出错: {str(e)}")
                
                # 更新连接状态
                if device_id in connection_status:
                    connection_status[device_id]["status"] = "error"
                    connection_status[device_id]["last_error"] = f"关闭连接失败: {str(e)}"
    return False

def close_all_connections() -> None:
    """关闭所有SSH连接"""
    for device_id in list(device_connections.keys()):
        close_connection(device_id)

def send_command(device_id: int, command: str, timeout: int = 30) -> Dict:
    """
    向设备发送命令并获取结果
    
    Args:
        device_id: 设备ID
        command: 要执行的命令
        timeout: 命令超时时间（秒）
        
    Returns:
        包含命令输出的字典
    """
    if device_id not in device_connections or device_connections[device_id] is None:
        return {
            'status': 'error',
            'message': '设备未连接',
            'output': ''
        }
        
    try:
        with connection_locks.get(device_id, threading.Lock()):
            output = device_connections[device_id].send_command(command, read_timeout=timeout)
            return {
                'status': 'success',
                'message': '命令执行成功',
                'output': output
            }
    except Exception as e:
        logger.error(f"设备 {device_id} 执行命令 '{command}' 失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'命令执行失败: {str(e)}',
            'output': ''
        }

def get_all_connections_status() -> Dict:
    """
    获取所有设备连接状态
    
    Returns:
        设备连接状态字典
    """
    result = {}
    for device_id in connection_status:
        result[device_id] = get_device_status(device_id)
    return result 