# 网络设备批量信息巡检功能说明文档

## 1. 功能概述

网络设备批量信息巡检功能旨在通过SSH协议自动登录到设备管理模块中的所有网络设备（路由器、交换机、防火墙等），收集设备状态信息，检查设备健康情况，并生成巡检报告。该功能采用多进程并发技术，能够高效地对大量设备进行并行巡检，显著提高巡检效率。

### 1.1 主要功能

- **网络设备批量SSH登录**：自动登录到所有网络设备并执行命令
- **设备状态信息收集**：收集CPU使用率、内存使用率、端口状态等信息
- **设备健康状态分析**：根据预设阈值判断设备状态是否异常
- **固件版本基线核查**：检查设备固件版本是否符合基线要求
- **自动生成巡检报告**：形成包含巡检结果统计的报告
- **异常情况自动报障**：对发现的异常情况自动创建故障记录

## 2. 系统架构

### 2.1 模块组成

该功能由以下几个主要模块组成：

1. **数据模型层**：定义巡检报告、巡检项等数据结构
2. **服务层**：实现设备信息收集、分析和处理逻辑
3. **接口层**：提供HTTP API接口供前端调用
4. **表现层**：实现巡检报告查看和管理的Web界面

### 2.2 关键组件

- **InspectionReport模型**：存储巡检报告基本信息和统计数据
- **InspectionItem模型**：存储每台设备的巡检结果详情
- **batch_info_collect函数**：批量巡检主函数，负责调度整个巡检流程
- **network_device_info_collect函数**：单设备信息收集函数
- **analyze_device_status函数**：设备状态分析函数

### 2.3 多进程并发架构

该功能采用Python的multiprocessing模块实现多进程并发，主要流程如下：

1. 主进程获取需要巡检的设备列表
2. 创建进程池，设置最大并发数
3. 为每台设备创建一个子进程执行巡检任务
4. 子进程完成后返回结果给主进程
5. 主进程汇总所有结果并生成报告

## 3. 数据模型设计

### 3.1 InspectionReport（巡检报告）模型

```python
class InspectionReport(BaseModel):
    """设备巡检报告模型"""
    __tablename__ = 'inspection_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 巡检报告标题
    start_time = db.Column(db.DateTime, nullable=False)  # 巡检开始时间
    end_time = db.Column(db.DateTime, nullable=False)  # 巡检结束时间
    total_devices = db.Column(db.Integer, default=0)  # 巡检设备总数
    successful_devices = db.Column(db.Integer, default=0)  # 巡检成功设备数
    failed_devices = db.Column(db.Integer, default=0)  # 巡检失败设备数
    abnormal_devices = db.Column(db.Integer, default=0)  # 异常设备数
    summary = db.Column(db.Text)  # 巡检总结
    operator = db.Column(db.String(50))  # 操作人
```

### 3.2 InspectionItem（巡检项）模型

```python
class InspectionItem(BaseModel):
    """设备巡检项模型"""
    __tablename__ = 'inspection_items'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('inspection_reports.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    status = db.Column(db.String(20), default='正常')  # 巡检状态：正常、异常、失败
    cpu_usage = db.Column(db.Float)  # CPU使用率
    memory_usage = db.Column(db.Float)  # 内存使用率
    uptime = db.Column(db.String(100))  # 设备运行时间
    firmware_version = db.Column(db.String(50))  # 固件版本
    port_usage = db.Column(db.Text)  # 端口使用情况(JSON)
    system_load = db.Column(db.Float)  # 系统负载
    error_message = db.Column(db.Text)  # 错误信息
    inspection_results = db.Column(db.Text)  # 巡检结果详情(JSON)
```

## 4. 巡检项目与阈值

系统对以下几个关键指标进行监控并设置了相应的阈值：

| 巡检项目 | 阈值 | 描述 |
|---------|------|------|
| CPU使用率 | 80% | CPU使用率超过80%视为异常 |
| 内存使用率 | 80% | 内存使用率超过80%视为异常 |
| 端口使用率 | 80% | 端口流量使用率超过80%视为异常 |
| 系统负载 | 0.7 | 系统负载超过0.7视为异常 |

此外，系统还维护了不同类型设备的固件版本基线：

| 设备类型 | 基线版本 |
|---------|---------|
| 路由器 | V800R021C10, V800R021C00 |
| 交换机 | V200R010C00, V200R010C10 |
| 防火墙 | V500R005C00, V500R005C10 |

## 5. 巡检流程

### 5.1 批量巡检主流程

1. 调用`batch_info_collect`函数启动巡检
2. 查询所有网络设备信息（路由器、交换机、防火墙）
3. 创建巡检报告记录
4. 创建多进程池，按设置的最大并发数执行巡检
5. 调用`network_device_info_collect`函数收集每台设备信息
6. 调用`analyze_device_status`函数分析设备状态
7. 将巡检结果保存到数据库
8. 生成巡检报告摘要

### 5.2 单设备巡检流程

1. 通过SSH登录到设备
2. 执行命令获取CPU使用率、内存使用率等信息
3. 获取设备接口状态和流量信息
4. 分析设备健康状态，判断是否存在异常
5. 如发现异常，自动创建故障记录

## 6. API接口说明

### 6.1 启动巡检

- **URL**: `/api/inspection/start`
- **方法**: POST
- **参数**:
  - `max_workers`: 最大并发数，默认为5
  - `operator`: 操作人员，默认为当前登录用户
- **响应**:
  ```json
  {
    "success": true,
    "message": "网络设备批量巡检已启动",
    "report_id": 123
  }
  ```

### 6.2 获取巡检报告列表

- **URL**: `/api/inspection/reports`
- **方法**: GET
- **响应**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 123,
        "title": "网络设备批量巡检报告 2023-06-01 10:30",
        "start_time": "2023-06-01T10:30:00",
        "end_time": "2023-06-01T10:35:00",
        "total_devices": 50,
        "successful_devices": 45,
        "failed_devices": 2,
        "abnormal_devices": 3,
        "operator": "admin"
      }
    ]
  }
  ```

### 6.3 获取巡检报告详情

- **URL**: `/api/inspection/reports/{report_id}`
- **方法**: GET
- **响应**:
  ```json
  {
    "success": true,
    "data": {
      "report": {
        "id": 123,
        "title": "网络设备批量巡检报告 2023-06-01 10:30",
        "start_time": "2023-06-01T10:30:00",
        "end_time": "2023-06-01T10:35:00",
        "total_devices": 50,
        "successful_devices": 45,
        "failed_devices": 2,
        "abnormal_devices": 3,
        "summary": "巡检报告：共巡检50台设备，正常45台，异常3台，无法连接2台。\n\n异常设备列表：\n- 交换机-A区-01: 发现2个异常项\n- 路由器-B区-02: 发现1个异常项\n- 防火墙-C区-01: 发现3个异常项",
        "operator": "admin"
      },
      "items": [
        {
          "id": 456,
          "report_id": 123,
          "device_id": 789,
          "device_name": "交换机-A区-01",
          "device_ip": "192.168.1.1",
          "status": "异常",
          "cpu_usage": 85.5,
          "memory_usage": 75.2,
          "uptime": "15 days, 7 hours, 23 minutes",
          "firmware_version": "V200R010C00",
          "system_load": 0.65
        }
      ]
    }
  }
  ```

## 7. 故障处理与报警

当巡检过程中发现设备存在异常时，系统会自动执行以下操作：

1. 将巡检项状态标记为"异常"
2. 在故障管理模块创建故障记录，包含异常详情
3. 根据异常数量确定故障严重程度：
   - 1-2个异常项: 中等严重度 (medium)
   - 3个或以上异常项: 高严重度 (high)

故障记录包含详细的异常信息描述，便于运维人员快速定位和解决问题。

## 8. 使用指南

### 8.1 启动巡检

1. 登录系统后，进入"维护管理" -> "巡检报告"页面
2. 点击"启动网络设备批量巡检"按钮
3. 在弹出的对话框中设置最大并发数和操作人员信息
4. 点击"确认启动"开始巡检
5. 巡检完成后，报告会自动显示在列表中

### 8.2 查看巡检报告

1. 在巡检报告列表中找到需要查看的报告
2. 点击"查看"按钮打开报告详情
3. 报告详情包含以下内容：
   - 报告基本信息（开始时间、结束时间、操作人等）
   - 巡检结果统计（总数、正常数、异常数、失败数）
   - 报告摘要（包含异常设备列表）
   - 巡检明细（所有设备的巡检结果）

### 8.3 查看设备巡检详情

1. 在巡检报告详情页的巡检明细表格中
2. 点击设备行末尾的"详情"按钮
3. 在弹出的对话框中可以看到：
   - 设备基本信息
   - 异常项列表（包含当前值、阈值和异常描述）
   - 正常项列表

## 9. 注意事项与最佳实践

1. **设备连接信息**：确保设备的IP地址、用户名和密码正确，否则无法进行巡检
2. **并发数设置**：根据服务器性能和网络情况调整最大并发数，建议不超过20
3. **阈值调整**：可根据实际环境在代码中调整`INSPECTION_THRESHOLDS`常量
4. **基线版本**：根据实际情况在代码中更新`FIRMWARE_BASELINE`字典
5. **异步处理**：在生产环境中，建议使用Celery等任务队列处理巡检任务，避免阻塞Web请求

## 10. 后续优化方向

1. **巡检策略定制**：支持自定义巡检设备范围和巡检项目
2. **自动定时巡检**：增加定时巡检功能，可配置巡检周期
3. **历史数据趋势分析**：基于多次巡检结果进行趋势分析
4. **邮件/短信通知**：检测到异常时主动发送通知给管理员
5. **设备配置核查**：增加设备配置一致性检查功能
6. **支持更多设备类型**：扩展对更多网络设备类型的支持

## 11. 技术实现细节

### 11.1 多进程池实现

```python
def batch_info_collect(max_workers: int = 5, operator: str = "系统") -> Optional[int]:
    # ...省略部分代码...
    
    # 创建进程池，并发执行巡检
    with multiprocessing.Pool(processes=max_workers) as pool:
        # 提交所有设备的巡检任务
        inspection_results = pool.map(network_device_info_collect, device_infos)
    
    # ...省略部分代码...
```

### 11.2 设备状态分析算法

```python
def analyze_device_status(device_result: Dict, device_info: Dict) -> Dict:
    abnormal_items = []
    normal_items = []
    
    # 检查CPU使用率
    if device_result['cpu_usage'] is not None:
        if device_result['cpu_usage'] > INSPECTION_THRESHOLDS['cpu_usage']:
            abnormal_items.append({
                'item': 'CPU使用率',
                'value': f"{device_result['cpu_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['cpu_usage']}%",
                'message': f"CPU使用率过高: {device_result['cpu_usage']}%"
            })
        else:
            normal_items.append({
                'item': 'CPU使用率',
                'value': f"{device_result['cpu_usage']}%",
                'threshold': f"{INSPECTION_THRESHOLDS['cpu_usage']}%",
                'message': '正常'
            })
    
    # ...省略其他检查项...
    
    return {
        'device_id': device_result['device_id'],
        'device_name': device_result['device_name'],
        'abnormal_items': abnormal_items,
        'normal_items': normal_items,
        'total_items': len(abnormal_items) + len(normal_items),
        'abnormal_count': len(abnormal_items)
    }
``` 