from flask import Flask, render_template, jsonify
from netmiko import ConnectHandler
import time
import re
import threading
import queue
import logging
import paramiko

app = Flask(__name__)

# 设备连接信息
DEVICE_INFO = {
    'device_type': 'huawei',
    'ip': '192.168.56.101',
    'username': 'prin',
    'password': 'Huawei@123',
    'port': 22,
    'timeout': 10,
    'keepalive': 30,  # 添加keepalive参数
    'session_timeout': 60,  # 会话超时时间
    'auto_connect': True,  # 自动重连
}

# 存储性能数据的队列
performance_data = queue.Queue(maxsize=100)
# 存储最新数据的变量
latest_data = {
    "cpu": 0,
    "memory": 0,
    "uptime": "",
    "timestamp": time.time(),
    "interfaces": {}
}

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 连接锁，防止多线程同时操作连接
connection_lock = threading.Lock()
# 当前连接对象
current_connection = None
# 上次连接时间
last_connection_time = 0

def get_connection():
    """获取或创建SSH连接"""
    global current_connection, last_connection_time
    
    with connection_lock:
        # 检查连接是否存在且有效
        if current_connection is not None:
            try:
                # 发送简单命令测试连接是否有效
                if hasattr(current_connection, 'find_prompt'):
                    current_connection.find_prompt()
                return current_connection
            except Exception as e:
                logger.warning(f"连接已失效，准备重新连接: {str(e)}")
                try:
                    current_connection.disconnect()
                except:
                    pass
                current_connection = None
        
        # 连接不存在或无效，创建新连接
        # 检查是否频繁重连（防止在短时间内多次重连）
        current_time = time.time()
        if current_time - last_connection_time < 5:
            time.sleep(5)  # 等待一段时间再重连
        
        try:
            logger.info("创建新连接...")
            # 修改SSH客户端设置
            ssh_conn = paramiko.SSHClient()
            ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 使用修改过的ConnectHandler
            device_params = DEVICE_INFO.copy()
            device_params['global_delay_factor'] = 2  # 增加全局延迟因子
            conn = ConnectHandler(**device_params)
            
            # 发送一个简单命令确认连接正常
            conn.find_prompt()
            
            current_connection = conn
            last_connection_time = time.time()
            logger.info("成功建立新连接")
            
            # 发送keep-alive配置命令（如果设备支持）
            try:
                conn.send_command("screen-length 0 temporary")  # 禁用分页
            except:
                pass
                
            return conn
        except Exception as e:
            logger.error(f"创建连接失败: {str(e)}")
            raise

def get_cpu_usage():
    """获取CPU使用率"""
    try:
        conn = get_connection()
        output = conn.send_command('display cpu-usage')
        match = re.search(r'CPU Usage\s+:\s+(\d+)%', output)
        if match:
            return int(match.group(1))
        return 0
    except Exception as e:
        logger.error(f"获取CPU使用率失败: {str(e)}")
        return 0

def get_memory_usage():
    """获取内存使用率"""
    try:
        conn = get_connection()
        output = conn.send_command('display memory-usage')
        match = re.search(r'Memory utilization\s+:\s+(\d+)%', output)
        if match:
            return int(match.group(1))
        return 0
    except Exception as e:
        logger.error(f"获取内存使用率失败: {str(e)}")
        return 0

def get_uptime():
    """获取设备运行时间"""
    try:
        conn = get_connection()
        output = conn.send_command('display version')
        match = re.search(r'Uptime is\s+(.+)', output)
        if match:
            return match.group(1)
        return "Unknown"
    except Exception as e:
        logger.error(f"获取设备运行时间失败: {str(e)}")
        return "Unknown"

def get_interface_stats():
    """获取接口统计信息"""
    interfaces = {}
    
    try:
        conn = get_connection()
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

def monitor_performance():
    """后台线程：持续监控设备性能"""
    global current_connection, latest_data
    
    # 设置监控间隔（秒）
    cpu_memory_interval = 10  # CPU和内存每10秒查询一次
    interface_interval = 30   # 接口信息每30秒查询一次
    
    last_interface_check = 0
    
    while True:
        try:
            # 1. 获取CPU和内存使用率
            cpu = get_cpu_usage()
            memory = get_memory_usage()
            
            # 2. 获取运行时间（频率低一些）
            uptime = get_uptime()
            
            # 3. 只在特定间隔获取接口信息（减少请求频率）
            current_time = time.time()
            if current_time - last_interface_check >= interface_interval:
                interfaces = get_interface_stats()
                last_interface_check = current_time
            else:
                # 重用上次的接口信息
                interfaces = latest_data.get('interfaces', {})
            
            # 更新最新数据
            timestamp = time.time()
            data = {
                "cpu": cpu,
                "memory": memory,
                "uptime": uptime,
                "interfaces": interfaces,
                "timestamp": timestamp
            }
            
            latest_data = data
            
            # 将数据放入队列
            if performance_data.full():
                performance_data.get()  # 移除最旧的数据
            performance_data.put(data)
            
            logger.info(f"获取性能数据: CPU {cpu}%, 内存 {memory}%")
            
            # 按照设定的间隔时间休眠
            time.sleep(cpu_memory_interval)
            
        except Exception as e:
            logger.error(f"监控过程中出错: {str(e)}")
            
            # 清理连接
            with connection_lock:
                if current_connection is not None:
                    try:
                        current_connection.disconnect()
                    except:
                        pass
                    current_connection = None
            
            # 休眠一段时间再重试
            time.sleep(10)

# 添加定期发送保活信号的线程
def keepalive_thread():
    """保持SSH连接活跃的线程"""
    while True:
        try:
            # 每25秒发送一个简单的保活命令
            if current_connection is not None:
                with connection_lock:
                    if current_connection is not None:
                        try:
                            # 发送对设备影响最小的命令
                            current_connection.send_command(" ")
                            logger.debug("发送保活信号")
                        except Exception as e:
                            logger.warning(f"保活失败: {str(e)}")
        except Exception as e:
            logger.warning(f"保活线程错误: {str(e)}")
        
        # 等待下一次保活
        time.sleep(25)

# 启动后台监控线程
monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
monitor_thread.start()

# 启动保活线程
keepalive_thread = threading.Thread(target=keepalive_thread, daemon=True)
keepalive_thread.start()

@app.route('/')
def index():
    """主页面，显示仪表盘"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API端点：返回最新性能数据"""
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    """API端点：返回历史性能数据"""
    history = list(performance_data.queue)
    return jsonify(history)

if __name__ == '__main__':
    # 确保目录结构
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # 启动Web服务器
    app.run(host='0.0.0.0', port=5000, debug=True) 