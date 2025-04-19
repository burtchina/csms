import paramiko
import time
import re
from src.db import db
from .models import PerformanceData
from src.modules.devices.models import Device

class PerformanceMonitor:
    """设备性能监控服务"""
    
    @staticmethod
    def collect_device_performance(device_id):
        """采集指定设备的性能数据"""
        device = Device.query.get(device_id)
        if not device:
            return None
            
        try:
            # 连接设备
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=device.ip_address,
                port=device.ssh_port or 22,
                username=device.username,
                password=device.password,
                timeout=10
            )
            
            # 采集CPU使用率
            _, stdout, _ = ssh_client.exec_command('display cpu-usage')
            cpu_output = stdout.read().decode('utf-8')
            cpu_usage = PerformanceMonitor._parse_cpu_usage(cpu_output)
            
            # 采集内存使用率
            _, stdout, _ = ssh_client.exec_command('display memory-usage')
            memory_output = stdout.read().decode('utf-8')
            memory_usage = PerformanceMonitor._parse_memory_usage(memory_output)
            
            # 获取设备运行时间
            _, stdout, _ = ssh_client.exec_command('display version')
            version_output = stdout.read().decode('utf-8')
            uptime = PerformanceMonitor._parse_uptime(version_output)
            
            ssh_client.close()
            
            # 创建性能数据记录
            perf_data = PerformanceData(
                device_id=device_id,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                bandwidth_usage=0.0,  # 默认值，可以在后续版本中实现带宽监控
                uptime=uptime,
                data_source='realtime'
            )
            
            db.session.add(perf_data)
            db.session.commit()
            
            return perf_data.to_dict()
            
        except Exception as e:
            # 处理连接或命令执行错误
            print(f"Error collecting performance data: {str(e)}")
            return {
                'device_id': device_id,
                'error': str(e),
                'cpu_usage': 0,
                'memory_usage': 0,
                'bandwidth_usage': 0,
                'uptime': 'Unknown',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
    
    @staticmethod
    def _parse_cpu_usage(output):
        """解析CPU使用率输出"""
        match = re.search(r'CPU usage: (\d+(\.\d+)?)%', output)
        if match:
            return float(match.group(1))
        return 0.0
    
    @staticmethod
    def _parse_memory_usage(output):
        """解析内存使用率输出"""
        match = re.search(r'Memory usage: (\d+(\.\d+)?)%', output)
        if match:
            return float(match.group(1))
        return 0.0
    
    @staticmethod
    def _parse_uptime(output):
        """解析设备运行时间"""
        match = re.search(r'uptime is (.*)', output)
        if match:
            return match.group(1)
        return "Unknown"
    
    @staticmethod
    def get_historical_data(device_id, hours=24):
        """获取指定设备的历史性能数据"""
        from datetime import datetime, timedelta
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        data = PerformanceData.query.filter(
            PerformanceData.device_id == device_id,
            PerformanceData.timestamp >= time_threshold
        ).order_by(PerformanceData.timestamp.asc()).all()
        
        return [item.to_dict() for item in data] 