# IPSec与防火墙联动策略管理数据模型设计

## 1. 数据库表设计

### 1.1 策略表（policy）

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY | 策略ID |
| name | VARCHAR(64) | NOT NULL | 策略名称 |
| type | VARCHAR(32) | NOT NULL | 策略类型（IPSec/SSL等） |
| description | TEXT | | 策略描述 |
| config | JSON | NOT NULL | 策略配置内容 |
| status | VARCHAR(16) | NOT NULL | 状态（draft/active/deleted） |
| created_by | INTEGER | NOT NULL, FK | 创建人ID，关联users表 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

### 1.2 策略模板表（policy_template）

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY | 模板ID |
| name | VARCHAR(64) | NOT NULL | 模板名称 |
| type | VARCHAR(32) | NOT NULL | 模板类型 |
| description | TEXT | | 模板描述 |
| config | JSON | NOT NULL | 模板配置内容 |
| is_system | BOOLEAN | NOT NULL | 是否系统预设模板 |
| created_by | INTEGER | FK | 创建人ID，关联users表 |
| created_at | DATETIME | NOT NULL | 创建时间 |

### 1.3 策略部署表（policy_deployment）

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY | 部署ID |
| policy_id | INTEGER | NOT NULL, FK | 策略ID，关联policy表 |
| device_id | INTEGER | NOT NULL, FK | 设备ID，关联devices表 |
| status | VARCHAR(16) | NOT NULL | 部署状态（pending/success/failed） |
| deployed_at | DATETIME | NOT NULL | 部署时间 |
| deployed_by | INTEGER | NOT NULL, FK | 部署人ID，关联users表 |
| config_snapshot | JSON | | 部署时的配置快照 |
| result | TEXT | | 部署结果信息 |

### 1.4 策略审计日志表（policy_audit_log）

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY | 日志ID |
| policy_id | INTEGER | FK | 策略ID，关联policy表 |
| user_id | INTEGER | NOT NULL, FK | 操作人ID，关联users表 |
| action | VARCHAR(32) | NOT NULL | 操作类型（create/update/delete/deploy/rollback） |
| details | TEXT | | 详细内容 |
| ip_address | VARCHAR(64) | | 操作IP地址 |
| created_at | DATETIME | NOT NULL | 操作时间 |

### 1.5 策略告警表（policy_alert）

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | INTEGER | PRIMARY KEY | 告警ID |
| policy_id | INTEGER | FK | 策略ID，关联policy表 |
| device_id | INTEGER | FK | 设备ID，关联devices表 |
| alert_type | VARCHAR(32) | NOT NULL | 告警类型（policy_violation/sync_failed等） |
| severity | VARCHAR(16) | NOT NULL | 严重程度（info/warning/critical） |
| details | TEXT | | 告警详情 |
| status | VARCHAR(16) | NOT NULL | 状态（new/acknowledged/resolved） |
| acknowledged_by | INTEGER | FK | 确认人ID，关联users表 |
| acknowledged_at | DATETIME | | 确认时间 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

## 2. SQLAlchemy ORM模型

### 2.1 Policy模型

```python
class Policy(Base):
    __tablename__ = 'policy'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    status = Column(String(16), nullable=False, default='draft')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship('User', backref='policies')
    deployments = relationship('PolicyDeployment', backref='policy', cascade='all, delete-orphan')
    audit_logs = relationship('PolicyAuditLog', backref='policy')
    alerts = relationship('PolicyAlert', backref='policy')
```

### 2.2 PolicyTemplate模型

```python
class PolicyTemplate(Base):
    __tablename__ = 'policy_template'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    type = Column(String(32), nullable=False)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    is_system = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    creator = relationship('User', backref='templates')
```

### 2.3 PolicyDeployment模型

```python
class PolicyDeployment(Base):
    __tablename__ = 'policy_deployment'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'), nullable=False)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    status = Column(String(16), nullable=False, default='pending')
    deployed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deployed_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    config_snapshot = Column(JSON)
    result = Column(Text)
    
    # 关系
    deployer = relationship('User', backref='deployments')
    device = relationship('Device', backref='policy_deployments')
```

### 2.4 PolicyAuditLog模型

```python
class PolicyAuditLog(Base):
    __tablename__ = 'policy_audit_log'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(32), nullable=False)
    details = Column(Text)
    ip_address = Column(String(64))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系
    user = relationship('User', backref='policy_audit_logs')
```

### 2.5 PolicyAlert模型

```python
class PolicyAlert(Base):
    __tablename__ = 'policy_alert'
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey('policy.id'))
    device_id = Column(Integer, ForeignKey('devices.id'))
    alert_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default='warning')
    details = Column(Text)
    status = Column(String(16), nullable=False, default='new')
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    acknowledger = relationship('User', backref='acknowledged_alerts')
    device = relationship('Device', backref='policy_alerts')
```

## 3. 配置数据结构

### 3.1 IPSec策略配置JSON结构

```json
{
  "version": "1.0",
  "firewall_settings": {
    "default_action": "deny",
    "allowed_protocols": [
      {
        "protocol": "udp",
        "port": 500,
        "description": "IKE"
      },
      {
        "protocol": "udp",
        "port": 4500,
        "description": "NAT-T"
      },
      {
        "protocol": "esp",
        "description": "ESP Protocol"
      }
    ]
  },
  "ipsec_settings": {
    "authentication": {
      "method": "psk",
      "psk": "encrypted:xxxxx"
    },
    "encryption": {
      "phase1": ["aes-256", "sha256", "dh-group14"],
      "phase2": ["aes-256", "sha256"]
    },
    "lifetime": {
      "phase1": 86400,
      "phase2": 3600
    }
  },
  "tunnel_settings": {
    "local_subnet": "192.168.1.0/24",
    "remote_subnet": "192.168.2.0/24",
    "remote_gateway": "203.0.113.1"
  },
  "source_restrictions": {
    "allowed_ips": ["203.0.113.0/24", "198.51.100.0/24"],
    "allowed_domains": ["partner-university.edu"]
  },
  "advanced": {
    "dpd_enabled": true,
    "dpd_delay": 30,
    "dpd_timeout": 120,
    "nat_traversal": true,
    "perfect_forward_secrecy": true
  }
}
```

### 3.2 IPSec+防火墙联动基本模板

```json
{
  "name": "IPSec基本安全策略",
  "type": "ipsec",
  "description": "仅允许IPSec相关协议通过，其他外部访问全部拒绝",
  "config": {
    "version": "1.0",
    "firewall_settings": {
      "default_action": "deny",
      "allowed_protocols": [
        {
          "protocol": "udp",
          "port": 500,
          "description": "IKE"
        },
        {
          "protocol": "udp",
          "port": 4500,
          "description": "NAT-T"
        },
        {
          "protocol": "esp",
          "description": "ESP Protocol"
        }
      ]
    },
    "ipsec_settings": {
      "authentication": {
        "method": "psk",
        "psk": ""
      },
      "encryption": {
        "phase1": ["aes-256", "sha256", "dh-group14"],
        "phase2": ["aes-256", "sha256"]
      },
      "lifetime": {
        "phase1": 86400,
        "phase2": 3600
      }
    },
    "tunnel_settings": {
      "local_subnet": "",
      "remote_subnet": "",
      "remote_gateway": ""
    },
    "source_restrictions": {
      "allowed_ips": [],
      "allowed_domains": []
    },
    "advanced": {
      "dpd_enabled": true,
      "dpd_delay": 30,
      "dpd_timeout": 120,
      "nat_traversal": true,
      "perfect_forward_secrecy": true
    }
  }
} 