# 校园安全管理系统(CSMS) API文档

## API概述

CSMS系统提供了一系列RESTful API，用于与系统进行交互，支持设备管理、故障处理、维护排期等功能。所有API请求和响应均使用JSON格式进行数据交换。系统API支持跨平台调用，便于集成到其他系统中。

## API基础信息

- **基础URL**: `/api/v1`
- **认证方式**: JWT Token (JSON Web Token)
- **内容类型**: `application/json`
- **版本控制**: 在URL中包含版本号(v1)，便于后续API升级

## 通用响应格式

所有API响应均遵循以下格式：

```json
{
  "status": "success|error",
  "message": "操作结果描述",
  "data": {
    // 响应数据（成功时）
  },
  "error": {
    "code": "错误代码",
    "details": "错误详情"
  }
}
```

## 认证

### 获取Token

```
POST /api/v1/auth/login
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| remember | boolean | 否 | 是否记住登录状态 |

**响应示例**:

```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-05-18T10:30:00Z",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true
    }
  }
}
```

### 刷新Token

```
POST /api/v1/auth/refresh
```

**请求头**:

```
Authorization: Bearer {refresh_token}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "Token已刷新",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-05-18T11:30:00Z",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 注销登录

```
POST /api/v1/auth/logout
```

**请求头**:

```
Authorization: Bearer {token}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "注销成功"
}
```

## 设备管理API

### 获取设备列表

```
GET /api/v1/devices
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| page | integer | 否 | 页码，默认为1 |
| per_page | integer | 否 | 每页记录数，默认为20 |
| category | string | 否 | 设备分类 |
| type_id | integer | 否 | 设备类型ID |
| status | string | 否 | 设备状态 |
| location | string | 否 | 设备位置 |
| search | string | 否 | 搜索关键词 |
| sort | string | 否 | 排序字段 |
| order | string | 否 | 排序方式(asc/desc) |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取设备列表成功",
  "data": {
    "devices": [
      {
        "id": 1,
        "name": "摄像头A区-01",
        "category": "camera",
        "type": {
          "id": 2,
          "name": "网络摄像机"
        },
        "model": "HK-2000",
        "status": "online",
        "location": "A区教学楼",
        "ip_address": "192.168.1.101",
        "last_maintenance": "2023-04-01T08:30:00Z"
      },
      {
        "id": 2,
        "name": "门禁系统B区-03",
        "category": "access_control",
        "type": {
          "id": 5,
          "name": "门禁控制器"
        },
        "model": "AC-500",
        "status": "online",
        "location": "B区宿舍楼",
        "ip_address": "192.168.1.102",
        "last_maintenance": "2023-03-15T14:20:00Z"
      }
    ],
    "pagination": {
      "total": 120,
      "per_page": 20,
      "current_page": 1,
      "last_page": 6,
      "from": 1,
      "to": 20
    }
  }
}
```

### 获取设备详情

```
GET /api/v1/devices/{device_id}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取设备详情成功",
  "data": {
    "id": 1,
    "name": "摄像头A区-01",
    "category": "camera",
    "type": {
      "id": 2,
      "name": "网络摄像机"
    },
    "model": "HK-2000",
    "status": "online",
    "location": "A区教学楼",
    "ip_address": "192.168.1.101",
    "mac_address": "00:1B:44:11:3A:B7",
    "firmware_version": "v2.3.5",
    "installation_date": "2022-08-15",
    "last_maintenance": "2023-04-01T08:30:00Z",
    "next_maintenance": "2023-07-01T08:30:00Z",
    "manufacturer": "海康威视",
    "serial_number": "SN20220815001",
    "description": "A区教学楼正门监控摄像头",
    "warranty_expiry": "2025-08-14",
    "specs": {
      "resolution": "1080p",
      "storage": "128GB",
      "power": "DC 12V"
    },
    "created_at": "2022-08-15T10:00:00Z",
    "updated_at": "2023-04-01T08:35:00Z"
  }
}
```

### 添加设备

```
POST /api/v1/devices
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| name | string | 是 | 设备名称 |
| category | string | 是 | 设备分类 |
| type_id | integer | 是 | 设备类型ID |
| model | string | 是 | 设备型号 |
| location | string | 是 | 设备位置 |
| ip_address | string | 否 | IP地址 |
| mac_address | string | 否 | MAC地址 |
| firmware_version | string | 否 | 固件版本 |
| installation_date | string | 否 | 安装日期(YYYY-MM-DD) |
| manufacturer | string | 否 | 制造商 |
| serial_number | string | 否 | 序列号 |
| description | string | 否 | 描述 |
| warranty_expiry | string | 否 | 保修到期日(YYYY-MM-DD) |
| specs | object | 否 | 设备规格参数 |

**响应示例**:

```json
{
  "status": "success",
  "message": "设备添加成功",
  "data": {
    "id": 121,
    "name": "摄像头C区-15",
    "category": "camera",
    "type_id": 2,
    "model": "HK-2000",
    "status": "offline",
    "location": "C区宿舍楼",
    "created_at": "2023-04-25T10:15:30Z"
  }
}
```

### 更新设备

```
PUT /api/v1/devices/{device_id}
```

**请求参数**: 同添加设备，所有参数均为可选

**响应示例**:

```json
{
  "status": "success",
  "message": "设备更新成功",
  "data": {
    "id": 1,
    "name": "摄像头A区-01(已升级)",
    "updated_at": "2023-04-25T14:30:25Z"
  }
}
```

### 删除设备

```
DELETE /api/v1/devices/{device_id}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "设备删除成功"
}
```

### 批量导入设备

```
POST /api/v1/devices/bulk-import
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| devices | array | 是 | 设备数据数组 |
| update_existing | boolean | 否 | 是否更新已存在的设备，默认false |

**响应示例**:

```json
{
  "status": "success",
  "message": "批量导入成功",
  "data": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "failures": [
      {
        "index": 3,
        "reason": "设备名称重复"
      },
      {
        "index": 7,
        "reason": "设备类型不存在"
      }
    ]
  }
}
```

### 获取设备类型列表

```
GET /api/v1/device-types
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取设备类型成功",
  "data": {
    "types": [
      {
        "id": 1,
        "name": "路由器",
        "description": "网络路由设备",
        "device_count": 15
      },
      {
        "id": 2,
        "name": "网络摄像机",
        "description": "监控摄像设备",
        "device_count": 42
      }
    ]
  }
}
```

## 设备通信API

### 执行设备命令

```
POST /api/v1/devices/{device_id}/command
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| command | string | 是 | 要执行的命令 |
| protocol | string | 否 | 通信协议(ssh/telnet)，默认ssh |
| timeout | integer | 否 | 超时时间(秒)，默认10 |

**响应示例**:

```json
{
  "status": "success",
  "message": "命令执行成功",
  "data": {
    "output": "命令执行结果...",
    "execution_time": 1.2
  }
}
```

### 获取设备状态信息

```
GET /api/v1/devices/{device_id}/status
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取状态成功",
  "data": {
    "online": true,
    "uptime": "10天14小时25分钟",
    "cpu_usage": 15.2,
    "memory_usage": 42.5,
    "temperature": 36.8,
    "last_checked": "2023-04-25T15:30:00Z"
  }
}
```

### 获取设备接口信息

```
GET /api/v1/devices/{device_id}/interfaces
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取接口信息成功",
  "data": {
    "interfaces": [
      {
        "name": "GigabitEthernet0/0",
        "status": "up",
        "ip_address": "192.168.1.1",
        "mac_address": "00:1A:2B:3C:4D:5E",
        "speed": "1Gbps",
        "in_traffic": 15.2,
        "out_traffic": 8.5
      },
      {
        "name": "GigabitEthernet0/1",
        "status": "down",
        "ip_address": null,
        "mac_address": "00:1A:2B:3C:4D:5F",
        "speed": "1Gbps",
        "in_traffic": 0,
        "out_traffic": 0
      }
    ]
  }
}
```

## 故障管理API

### 获取故障列表

```
GET /api/v1/faults
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| page | integer | 否 | 页码，默认为1 |
| per_page | integer | 否 | 每页记录数，默认为20 |
| device_id | integer | 否 | 设备ID |
| status | string | 否 | 故障状态(pending/processing/resolved) |
| severity | string | 否 | 严重程度(low/medium/high/critical) |
| start_date | string | 否 | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | 结束日期(YYYY-MM-DD) |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取故障列表成功",
  "data": {
    "faults": [
      {
        "id": 1,
        "title": "摄像头离线",
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "fault_type": "connection_failure",
        "severity": "high",
        "status": "resolved",
        "reported_by": "admin",
        "created_at": "2023-04-10T08:15:00Z",
        "updated_at": "2023-04-10T10:30:00Z"
      },
      {
        "id": 2,
        "title": "门禁系统异常",
        "device_id": 2,
        "device_name": "门禁系统B区-03",
        "fault_type": "hardware_failure",
        "severity": "critical",
        "status": "processing",
        "reported_by": "operator1",
        "created_at": "2023-04-15T14:20:00Z",
        "updated_at": "2023-04-15T15:10:00Z"
      }
    ],
    "pagination": {
      "total": 35,
      "per_page": 20,
      "current_page": 1,
      "last_page": 2,
      "from": 1,
      "to": 20
    }
  }
}
```

### 报告故障

```
POST /api/v1/faults
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| title | string | 是 | 故障标题 |
| device_id | integer | 是 | 设备ID |
| fault_type | string | 是 | 故障类型 |
| severity | string | 是 | 严重程度(low/medium/high/critical) |
| description | string | 是 | 故障描述 |
| attachments | array | 否 | 附件文件ID数组 |

**响应示例**:

```json
{
  "status": "success",
  "message": "故障报告创建成功",
  "data": {
    "id": 36,
    "title": "交换机端口故障",
    "status": "pending",
    "created_at": "2023-04-25T16:45:00Z"
  }
}
```

## 维护管理API

### 获取维护计划列表

```
GET /api/v1/maintenance
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| page | integer | 否 | 页码，默认为1 |
| per_page | integer | 否 | 每页记录数，默认为20 |
| device_id | integer | 否 | 设备ID |
| status | string | 否 | 维护状态(planned/inprogress/completed/cancelled) |
| start_date | string | 否 | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | 结束日期(YYYY-MM-DD) |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取维护计划列表成功",
  "data": {
    "maintenance_plans": [
      {
        "id": 1,
        "title": "摄像头季度检查",
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "maintenance_type": "routine",
        "status": "completed",
        "assigned_to": "technician1",
        "start_time": "2023-04-01T08:00:00Z",
        "end_time": "2023-04-01T09:00:00Z",
        "created_at": "2023-03-15T10:20:00Z"
      },
      {
        "id": 2,
        "title": "门禁系统固件升级",
        "device_id": 2,
        "device_name": "门禁系统B区-03",
        "maintenance_type": "upgrade",
        "status": "planned",
        "assigned_to": "technician2",
        "start_time": "2023-04-30T14:00:00Z",
        "end_time": "2023-04-30T16:00:00Z",
        "created_at": "2023-04-15T11:30:00Z"
      }
    ],
    "pagination": {
      "total": 28,
      "per_page": 20,
      "current_page": 1,
      "last_page": 2,
      "from": 1,
      "to": 20
    }
  }
}
```

## 性能监控API

### 获取性能指标列表

```
GET /api/v1/performance/metrics
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取性能指标列表成功",
  "data": {
    "metrics": [
      {
        "id": "cpu_usage",
        "name": "CPU使用率",
        "unit": "%",
        "description": "设备CPU使用百分比"
      },
      {
        "id": "memory_usage",
        "name": "内存使用率",
        "unit": "%",
        "description": "设备内存使用百分比"
      },
      {
        "id": "temperature",
        "name": "温度",
        "unit": "°C",
        "description": "设备工作温度"
      }
    ]
  }
}
```

### 获取设备性能数据

```
GET /api/v1/devices/{device_id}/performance
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| metrics | string | 否 | 指标ID列表，用逗号分隔 |
| start_time | string | 否 | 开始时间(ISO8601格式) |
| end_time | string | 否 | 结束时间(ISO8601格式) |
| interval | string | 否 | 时间间隔(minute/hour/day)，默认hour |
| limit | integer | 否 | 返回数据点数量限制，默认100 |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取性能数据成功",
  "data": {
    "device_id": 1,
    "device_name": "摄像头A区-01",
    "start_time": "2023-04-24T00:00:00Z",
    "end_time": "2023-04-24T23:59:59Z",
    "interval": "hour",
    "metrics": {
      "cpu_usage": [
        {
          "timestamp": "2023-04-24T00:00:00Z",
          "value": 12.5
        },
        {
          "timestamp": "2023-04-24T01:00:00Z",
          "value": 15.2
        }
      ],
      "memory_usage": [
        {
          "timestamp": "2023-04-24T00:00:00Z",
          "value": 35.8
        },
        {
          "timestamp": "2023-04-24T01:00:00Z",
          "value": 36.2
        }
      ]
    }
  }
}
```

### 设置性能阈值

```
POST /api/v1/devices/{device_id}/thresholds
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| metric_id | string | 是 | 指标ID |
| warning_threshold | number | 否 | 警告阈值 |
| critical_threshold | number | 否 | 严重阈值 |
| enabled | boolean | 否 | 是否启用，默认true |

**响应示例**:

```json
{
  "status": "success",
  "message": "阈值设置成功",
  "data": {
    "id": 12,
    "device_id": 1,
    "metric_id": "cpu_usage",
    "warning_threshold": 70,
    "critical_threshold": 90,
    "enabled": true,
    "created_at": "2023-04-25T17:30:00Z"
  }
}
```

### 获取设备告警列表

```
GET /api/v1/devices/{device_id}/alerts
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| page | integer | 否 | 页码，默认为1 |
| per_page | integer | 否 | 每页记录数，默认为20 |
| status | string | 否 | 告警状态(active/acknowledged/resolved) |
| severity | string | 否 | 严重程度(warning/critical) |
| start_time | string | 否 | 开始时间(ISO8601格式) |
| end_time | string | 否 | 结束时间(ISO8601格式) |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取告警列表成功",
  "data": {
    "alerts": [
      {
        "id": 1,
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "metric_id": "cpu_usage",
        "metric_name": "CPU使用率",
        "value": 75.2,
        "threshold": 70,
        "severity": "warning",
        "status": "active",
        "created_at": "2023-04-24T15:30:00Z",
        "updated_at": "2023-04-24T15:30:00Z"
      },
      {
        "id": 2,
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "metric_id": "temperature",
        "metric_name": "温度",
        "value": 45.8,
        "threshold": 40,
        "severity": "critical",
        "status": "acknowledged",
        "created_at": "2023-04-24T16:15:00Z",
        "updated_at": "2023-04-24T16:30:00Z"
      }
    ],
    "pagination": {
      "total": 5,
      "per_page": 20,
      "current_page": 1,
      "last_page": 1,
      "from": 1,
      "to": 5
    }
  }
}
```

## 系统设置API

### 获取用户列表

```
GET /api/v1/users
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取用户列表成功",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": true,
        "created_at": "2023-03-01T10:00:00Z"
      },
      {
        "id": 2,
        "username": "operator1",
        "email": "operator1@example.com",
        "role": "operator",
        "is_active": true,
        "created_at": "2023-03-05T14:20:00Z"
      }
    ]
  }
}
```

### 获取系统配置

```
GET /api/v1/settings
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取系统配置成功",
  "data": {
    "settings": {
      "site_name": "校园安全管理系统",
      "device_polling_interval": 300,
      "alert_notification_channels": ["email", "sms"],
      "maintenance_reminder_days": 7,
      "default_pagination_size": 20
    }
  }
}
```

## 错误处理

### 常见错误码

| 错误码 | 描述 |
|-------|------|
| 400 | 请求参数错误 |
| 401 | 未授权(未登录或token无效) |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 请求实体无法处理 |
| 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "status": "error",
  "message": "设备不存在",
  "error": {
    "code": 404,
    "details": "无法找到ID为123的设备"
  }
}
```

## API限制

- 每个IP地址每分钟最多允许100次请求
- 身份验证API每个IP地址每小时最多允许10次失败尝试
- 每次请求最大数据大小为10MB
- 文件上传API每次请求最大文件大小为50MB

## 版本历史

| 版本 | 发布日期 | 说明 |
|-----|---------|-----|
| v1.0.0 | 2023-03-15 | 初始版本 |
| v1.1.0 | 2023-04-10 | 添加设备批量导入API |
| v1.2.0 | 2023-04-25 | 添加性能监控和设备通信API | 