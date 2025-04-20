# 校园安全管理系统(CSMS) API文档

## API概述

CSMS系统提供了一系列RESTful API，用于与系统进行交互，支持设备管理、故障处理、维护排期等功能。所有API请求和响应均使用JSON格式进行数据交换。

## API基础信息

- **基础URL**: `/api/v1`
- **认证方式**: JWT Token (JSON Web Token)
- **内容类型**: `application/json`

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

**响应示例**:

```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-05-18T10:30:00Z",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "is_admin": true
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
Authorization: Bearer {token}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "Token已刷新",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2023-05-18T11:30:00Z"
  }
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
| status | string | 否 | 设备状态 |
| location | string | 否 | 设备位置 |
| search | string | 否 | 搜索关键词 |

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
| model | string | 是 | 设备型号 |
| location | string | 是 | 设备位置 |
| ip_address | string | 否 | IP地址 |
| mac_address | string | 否 | MAC地址 |
| ... | ... | ... | ... |

**响应示例**:

```json
{
  "status": "success",
  "message": "设备添加成功",
  "data": {
    "id": 121,
    "name": "摄像头C区-15",
    "category": "camera",
    "model": "HK-2000",
    "status": "offline",
    "location": "C区食堂",
    "ip_address": "192.168.1.120",
    "created_at": "2023-05-18T09:30:00Z",
    "updated_at": "2023-05-18T09:30:00Z"
  }
}
```

### 更新设备

```
PUT /api/v1/devices/{device_id}
```

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|-----|------|
| name | string | 否 | 设备名称 |
| status | string | 否 | 设备状态 |
| location | string | 否 | 设备位置 |
| ... | ... | ... | ... |

**响应示例**:

```json
{
  "status": "success",
  "message": "设备更新成功",
  "data": {
    "id": 1,
    "name": "摄像头A区-01-更新",
    "category": "camera",
    "model": "HK-2000",
    "status": "maintenance",
    "location": "A区教学楼",
    "updated_at": "2023-05-18T09:45:00Z"
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
  "message": "设备删除成功",
  "data": null
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
| status | string | 否 | 故障状态 |
| priority | string | 否 | 故障优先级 |
| device_id | integer | 否 | 设备ID |

**响应示例**:

```json
{
  "status": "success",
  "message": "获取故障列表成功",
  "data": {
    "faults": [
      {
        "id": "F001",
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "type": "signal_loss",
        "description": "视频信号丢失",
        "status": "pending",
        "priority": "high",
        "reported_at": "2023-04-15T08:30:00Z",
        "reported_by": "system"
      },
      {
        "id": "F002",
        "device_id": 2,
        "device_name": "门禁系统B区-03",
        "type": "hardware_failure",
        "description": "读卡器故障",
        "status": "in_progress",
        "priority": "medium",
        "reported_at": "2023-04-16T13:45:00Z",
        "reported_by": "user_id_5"
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

## 维护管理API

### 获取维护计划

```
GET /api/v1/maintenance
```

**响应示例**:

```json
{
  "status": "success",
  "message": "获取维护计划成功",
  "data": {
    "maintenance_plans": [
      {
        "id": 1,
        "device_id": 1,
        "device_name": "摄像头A区-01",
        "type": "routine",
        "description": "例行检查和清洁",
        "scheduled_at": "2023-07-01T08:30:00Z",
        "duration": 60,
        "assigned_to": "user_id_8",
        "status": "scheduled"
      }
    ],
    "pagination": {
      "total": 45,
      "per_page": 20,
      "current_page": 1,
      "last_page": 3,
      "from": 1,
      "to": 20
    }
  }
}
```

## 错误处理

所有API可能的错误响应：

### 验证错误

```json
{
  "status": "error",
  "message": "请求参数验证失败",
  "errors": {
    "name": ["设备名称为必填项"],
    "ip_address": ["IP地址格式不正确"]
  }
}
```

### 认证错误

```json
{
  "status": "error",
  "message": "认证失败",
  "error_code": "authentication_failed"
}
```

### 权限错误

```json
{
  "status": "error",
  "message": "没有权限执行此操作",
  "error_code": "permission_denied"
}
```

### 资源不存在

```json
{
  "status": "error",
  "message": "请求的资源不存在",
  "error_code": "resource_not_found"
}
```

### 服务器错误

```json
{
  "status": "error",
  "message": "服务器内部错误",
  "error_code": "internal_server_error"
}
```

## API状态码

| 状态码 | 描述 |
|-------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或Token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 参数验证错误 |
| 500 | 服务器内部错误 |

## API版本控制

本系统API采用URI版本控制，当前版本为v1。未来版本更新将通过URI中的版本号进行区分，如`/api/v2/...`。

## 开发注意事项

### 1. Jinja2模板中的集合长度

在Jinja2模板中处理集合长度（如设备列表数量）时，请使用`|length`过滤器而非Python内置的`len()`函数：

**正确用法**:
```html
<!-- 获取设备数量 -->
<td>{{ devices|length }}</td>
<td>{{ device_type.devices|length }}</td>
```

**错误用法**:
```html
<!-- 这会导致500服务器错误! -->
<td>{{ len(devices) }}</td>
<td>{{ len(device_type.devices) }}</td>
```

这一点在处理设备类型和关联设备数量显示时尤为重要。 