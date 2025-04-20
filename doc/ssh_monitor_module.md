# SSH监控模块设计与实现文档

## 1. 模块概述

SSH监控模块(`src/modules/performance/ssh_monitor.py`)是系统中负责与网络设备建立SSH连接并获取性能数据的核心组件。该模块实现了设备连接管理、性能数据采集和连接资源管理等功能，为系统提供了与网络设备交互的基础能力。

### 1.1 主要功能

- **连接管理**：创建、维护、复用和关闭与网络设备的SSH连接
- **性能数据采集**：获取设备CPU使用率、内存使用率、运行时间和接口统计信息
- **模拟模式**：当无法连接到真实设备时提供模拟数据，便于开发和测试
- **多线程支持**：通过线程锁确保多线程环境下的连接安全
- **批量数据采集**：支持并发采集多个设备的性能数据

## 2. 模块设计

### 2.1 核心数据结构

模块维护了三个全局字典来管理设备连接：

```python
# 连接锁，防止多线程同时操作连接
connection_locks = {}  # 格式: {device_id: threading.Lock()}
# 当前连接对象
device_connections = {}  # 格式: {device_id: connection_object}
# 上次连接时间
last_connection_times = {}  # 格式: {device_id: timestamp}
```

### 2.2 关键函数

| 函数名 | 功能描述 |
|--------|----------|
| `get_connection()` | 获取或创建到设备的SSH连接 |
| `get_cpu_usage()` | 获取设备CPU使用率 |
| `get_memory_usage()` | 获取设备内存使用率 |
| `get_uptime()` | 获取设备运行时间 |
| `get_interface_stats()` | 获取设备接口统计信息 |
| `collect_device_data()` | 收集单个设备的所有性能数据 |
| `batch_collect_data()` | 批量收集多个设备的性能数据 |
| `close_connection()` | 关闭指定设备的连接 |
| `close_all_connections()` | 关闭所有设备连接 |

### 2.3 模拟模式

模块实现了模拟模式，通过全局变量`SIMULATION_MODE`控制。当模拟模式启用且无法连接到真实设备时，模块会返回模拟的性能数据，确保系统功能正常运行。

```python
# 启用模拟模式（当无法连接到真实设备时，返回模拟数据）
SIMULATION_MODE = True
```

## 3. 与设备服务模块的集成

### 3.1 设备服务模块如何使用SSH监控

`src/modules/device/services.py`中的设备服务模块主要通过以下两个函数使用SSH监控功能：

#### 3.1.1 测试设备连接

```python
def test_device_connection(device_id: int) -> Dict:
    """测试设备连接"""
    device = get_device_by_id(device_id)
    if not device:
        return {'success': False, 'message': f'设备ID {device_id} 不存在'}
    
    # 检查设备是否有IP地址
    if not device.ip_address:
        return {'success': False, 'message': f'设备 {device.name} 没有配置IP地址'}
    
    try:
        # 尝试SSH连接
        connection = get_connection(
            device_id, 
            device.ip_address, 
            device.username or 'admin', 
            device.password or 'admin123',
            device.port or 22
        )
        
        if not connection:
            return {'success': False, 'message': f'无法连接到设备 {device.name} ({device.ip_address})'}
        
        # 测试获取设备信息
        uptime = get_uptime(device_id, connection)
        
        # 关闭连接
        close_connection(device_id)
        
        return {'success': True, 'message': f'成功连接到设备 {device.name}', 'uptime': uptime}
    except Exception as e:
        logger.error(f"测试设备 {device_id} 连接时出错: {str(e)}")
        return {'success': False, 'message': f'连接测试出错: {str(e)}'}
```

#### 3.1.2 获取设备详细信息

```python
def get_device_info(device_id: int) -> Dict:
    """获取设备详细信息"""
    device = get_device_by_id(device_id)
    if not device:
        return {'success': False, 'message': f'设备ID {device_id} 不存在'}
    
    try:
        # 基本设备信息
        result = {'success': True, 'device': device.to_dict()}
        
        # 如果设备可连接，尝试获取更多信息
        if device.ip_address and device.status == '正常':
            try:
                # 尝试SSH连接
                connection = get_connection(
                    device_id, 
                    device.ip_address, 
                    device.username or 'admin', 
                    device.password or 'admin123',
                    device.port or 22
                )
                
                if connection:
                    # 获取设备信息
                    result['connection_status'] = 'connected'
                    result['uptime'] = get_uptime(device_id, connection)
                    result['cpu_usage'] = get_cpu_usage(device_id, connection)
                    result['memory_usage'] = get_memory_usage(device_id, connection)
                    result['interfaces'] = get_interface_stats(device_id, connection)
                    
                    # 关闭连接
                    close_connection(device_id)
                else:
                    result['connection_status'] = 'failed'
            except Exception as e:
                logger.error(f"获取设备 {device_id} 详细信息时出错: {str(e)}")
                result['connection_status'] = 'error'
                result['connection_error'] = str(e)
        else:
            result['connection_status'] = 'unavailable'
        
        return result
    
    except Exception as e:
        logger.error(f"获取设备 {device_id} 信息时出错: {str(e)}")
        return {'success': False, 'message': f'获取设备信息出错: {str(e)}'}
```

### 3.2 RESTful API接口

设备服务模块通过`src/modules/device/routes.py`提供了多个RESTful API接口，允许前端应用访问设备信息和测试设备连接：

```python
@device_bp.route('/api/info/<int:device_id>')
def api_device_info(device_id):
    """获取设备详细信息API"""
    try:
        result = get_device_info(device_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result})
        else:
            return jsonify({'status': 'error', 'message': result.get('message', '未知错误')}), 404
    except Exception as e:
        logger.error(f"获取设备 {device_id} 信息时出错: {str(e)}")
        return jsonify({'status': 'error', 'message': f'获取设备信息失败: {str(e)}'}), 500

@device_bp.route('/api/test-connection/<int:device_id>')
def api_test_connection(device_id):
    """测试设备连接API"""
    try:
        result = test_device_connection(device_id)
        if result.get('success'):
            return jsonify({'status': 'success', 'data': result})
        else:
            return jsonify({'status': 'error', 'message': result.get('message', '未知错误')}), 400
    except Exception as e:
        logger.error(f"测试设备 {device_id} 连接时出错: {str(e)}")
        return jsonify({'status': 'error', 'message': f'测试连接失败: {str(e)}'}), 500
```

## 4. 实现细节

### 4.1 连接管理

SSH监控模块实现了智能的连接管理策略：

1. **连接复用**：已建立的连接会被缓存，避免频繁创建新连接
2. **连接有效性检测**：每次获取连接时会检查连接是否有效
3. **重连延迟**：防止短时间内多次重连，避免资源耗尽
4. **线程安全**：使用线程锁确保并发安全
5. **自动清理**：连接使用完毕后自动关闭

### 4.2 命令执行模式

针对不同的设备信息采集，模块使用特定的命令：

| 功能 | 命令 | 正则解析 |
|------|------|----------|
| CPU使用率 | `display cpu-usage` | `CPU Usage\s+:\s+(\d+)%` |
| 内存使用率 | `display memory-usage` | `Memory utilization\s+:\s+(\d+)%` |
| 运行时间 | `display version` | `Uptime is\s+(.+)` |
| 接口状态 | `display interface brief` | 多行解析 |
| 接口详情 | `display interface {interface}` | 多正则匹配 |

### 4.3 模拟数据生成

模拟模式下，模块会生成合理的随机数据：

- CPU使用率：10%-90%
- 内存使用率：20%-85%
- 运行时间：1-365天的随机时间
- 接口状态：80%概率为up状态
- 接口流量：1Kbps-1Mbps随机值

### 4.4 错误处理

模块实现了全面的错误处理机制：

1. **连接失败处理**：自动切换到模拟模式或返回错误信息
2. **命令执行错误**：记录错误日志并返回默认值
3. **数据解析异常**：优雅降级，返回可用的部分数据
4. **资源清理**：即使发生异常也确保连接资源被释放

## 5. 性能考虑

### 5.1 连接池化

模块实现了简单的连接池，通过`device_connections`字典缓存和复用连接对象，减少连接建立的开销。

### 5.2 多线程数据采集

`batch_collect_data`函数使用多线程并发采集多个设备的数据，提高数据采集效率：

```python
def batch_collect_data(devices: list) -> Dict:
    """批量收集多个设备的性能数据"""
    results = {}
    threads = []
    
    # 使用线程池并发收集数据
    for device in devices:
        # ... 参数准备 ...
        
        # 创建线程收集数据
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
```

### 5.3 连接优化

模块通过以下方式优化连接性能：

1. 设置连接超时：避免长时间挂起
2. 启用keepalive：保持连接活跃
3. 禁用分页：避免因分页等待导致的命令执行延迟
4. 延迟重连：防止频繁重连导致的资源消耗

## 6. 使用示例

### 6.1 测试设备连接

```python
# 导入必要模块
from src.modules.device.services import test_device_connection

# 测试ID为1的设备连接
result = test_device_connection(1)

if result['success']:
    print(f"连接成功! 设备运行时间: {result['uptime']}")
else:
    print(f"连接失败: {result['message']}")
```

### 6.2 获取设备详细信息

```python
# 导入必要模块
from src.modules.device.services import get_device_info

# 获取ID为1的设备信息
result = get_device_info(1)

if result['success']:
    device = result['device']
    print(f"设备名称: {device['name']}")
    print(f"IP地址: {device['ip_address']}")
    
    if 'cpu_usage' in result:
        print(f"CPU使用率: {result['cpu_usage']}%")
    
    if 'memory_usage' in result:
        print(f"内存使用率: {result['memory_usage']}%")
    
    if 'interfaces' in result:
        print(f"接口数量: {len(result['interfaces'])}")
else:
    print(f"获取设备信息失败: {result['message']}")
```

## 7. 最佳实践

1. **总是关闭连接**：使用完连接后调用`close_connection`释放资源
2. **错误处理**：捕获并处理可能的异常，确保模块正常工作
3. **连接身份验证**：确保提供正确的用户名和密码
4. **合理使用模拟模式**：开发和测试环境启用模拟模式，生产环境禁用
5. **监控连接状态**：定期检查连接状态，及时释放无效连接

## 8. 注意事项

1. 模块依赖`netmiko`库，如未安装会自动降级为模拟模式
2. 默认支持华为设备命令，使用其他厂商设备可能需要调整命令和解析逻辑
3. 模拟模式下，性能数据为随机生成，仅用于开发和测试
4. 批量数据采集使用多线程，注意控制并发数量，避免资源耗尽
5. 网络设备可能有命令执行限制，需根据实际情况调整请求频率

## 9. 未来改进

1. 支持更多网络设备厂商和型号
2. 实现更完善的连接池管理
3. 添加更多性能指标采集
4. 支持SNMP协议作为SSH的备选
5. 实现基于事件的异步数据采集
6. 支持设备配置管理功能
7. 添加数据缓存减少设备查询频率 