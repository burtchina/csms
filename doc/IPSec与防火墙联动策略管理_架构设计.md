# IPSec与防火墙联动策略管理架构设计

## 1. 模块结构

基于校园安全管理系统现有架构，IPSec与防火墙联动策略管理功能作为安全策略管理子系统，包含以下核心模块：

### 1.1 策略管理模块（PolicyManager）
- 职责：负责策略的创建、更新、删除和查询
- 核心类：
  - PolicyService：策略业务逻辑服务
  - PolicyRepository：策略数据访问层
  - PolicyValidator：策略参数验证器

### 1.2 策略下发与同步模块（PolicyDeployer）
- 职责：负责将策略下发到防火墙设备并同步状态
- 核心类：
  - PolicyDeployService：策略下发业务逻辑
  - FirewallConnector：防火墙连接适配器（支持多厂商）
  - PolicySyncScheduler：策略同步调度器

### 1.3 策略审计与日志模块（PolicyAudit）
- 职责：记录策略变更操作，提供审计查询
- 核心类：
  - PolicyAuditService：审计业务逻辑
  - AuditLogRepository：日志数据访问层
  - AuditExporter：审计日志导出器

### 1.4 异常检测与告警模块（PolicyAlert）
- 职责：监控策略生效状态，发现异常自动告警
- 核心类：
  - PolicyMonitorService：策略监控服务
  - AlertGenerator：告警生成器
  - AlertNotifier：告警通知器

### 1.5 Web接口模块
- 职责：提供RESTful API接口
- 核心类：
  - PolicyController：策略管理API控制器
  - PolicyAuditController：审计日志API控制器
  - PolicyAlertController：告警API控制器

## 2. 数据流

### 2.1 策略配置流程
```
管理员 -> Web界面 -> PolicyController -> PolicyService -> PolicyRepository -> 数据库
```

### 2.2 策略下发流程
```
管理员 -> Web界面 -> PolicyController -> PolicyDeployService -> FirewallConnector -> 防火墙设备
                                      |
                                      v
                                PolicyAuditService -> AuditLogRepository -> 数据库
```

### 2.3 策略监控流程
```
PolicySyncScheduler -> PolicyMonitorService -> FirewallConnector -> 防火墙设备
                                            |
                                            v
                                   (发现异常) AlertGenerator -> AlertNotifier -> 管理员
                                                            |
                                                            v
                                                  PolicyAlertRepository -> 数据库
```

## 3. 与现有系统集成方案

### 3.1 模块集成
- 在`src/modules`目录下新建`policy`子目录，存放策略管理相关模块
- 目录结构：
  ```
  src/modules/policy/
  ├── __init__.py
  ├── models/           # 数据模型
  ├── services/         # 业务逻辑
  ├── repositories/     # 数据访问
  ├── validators/       # 参数验证
  ├── connectors/       # 设备连接适配器
  └── routes/           # API路由
  ```

### 3.2 数据库集成
- 在现有数据库中添加新表：policy, policy_template, policy_audit_log, policy_alert_log
- 通过SQLAlchemy ORM模型关联已有的设备表和用户表

### 3.3 用户界面集成
- 在导航菜单中添加"安全策略"板块
- 策略相关页面包括：策略列表、策略详情、策略编辑、模板管理、审计日志、告警管理

### 3.4 权限集成
- 扩展现有RBAC权限模型，添加策略管理相关权限：
  - policy:view - 查看策略
  - policy:create - 创建策略
  - policy:edit - 编辑策略
  - policy:delete - 删除策略
  - policy:deploy - 下发策略
  - policy:audit - 查看审计日志

## 4. 接口设计

### 4.1 内部接口

#### PolicyService
```python
class PolicyService:
    def create_policy(self, policy_data, user_id):
        """创建新策略"""
        
    def update_policy(self, policy_id, policy_data, user_id):
        """更新策略"""
        
    def delete_policy(self, policy_id, user_id):
        """删除策略"""
        
    def get_policy(self, policy_id):
        """获取单个策略详情"""
        
    def list_policies(self, filters=None):
        """获取策略列表"""
```

#### PolicyDeployService
```python
class PolicyDeployService:
    def deploy_policy(self, policy_id, device_id, user_id):
        """部署策略到设备"""
        
    def rollback_policy(self, policy_id, device_id, user_id):
        """回滚策略"""
        
    def get_policy_status(self, policy_id, device_id):
        """获取策略部署状态"""
```

### 4.2 外部接口（RESTful API）

#### 策略管理
- `GET /api/policies` - 获取策略列表
- `POST /api/policies` - 创建新策略
- `GET /api/policies/{id}` - 获取策略详情
- `PUT /api/policies/{id}` - 更新策略
- `DELETE /api/policies/{id}` - 删除策略

#### 策略部署
- `POST /api/policies/{id}/deploy` - 部署策略到设备
- `POST /api/policies/{id}/rollback` - 回滚策略
- `GET /api/policies/{id}/status` - 获取策略状态

#### 审计日志
- `GET /api/policy-audit-logs` - 获取审计日志
- `GET /api/policy-audit-logs/export` - 导出审计日志

#### 告警管理
- `GET /api/policy-alerts` - 获取告警列表
- `PUT /api/policy-alerts/{id}` - 更新告警状态

## 5. 异常处理与容错设计

### 5.1 策略验证机制
- 在策略创建和更新时进行参数验证
- 在策略下发前进行设备兼容性验证
- 支持策略测试模式，验证策略有效性

### 5.2 策略下发失败处理
- 采用事务处理，确保策略下发原子性
- 提供自动回滚机制，下发失败自动恢复
- 详细记录失败原因，便于问题排查

### 5.3 设备连接异常处理
- 设备连接超时重试机制
- 连接失败后的降级处理
- 设备状态定期检测与恢复

## 6. 扩展性设计

### 6.1 设备适配器架构
采用适配器模式，支持不同厂商防火墙设备：

```python
class FirewallConnector(ABC):
    @abstractmethod
    def connect(self, device):
        pass
        
    @abstractmethod
    def deploy_policy(self, device, policy):
        pass
        
    @abstractmethod
    def get_policy_status(self, device, policy):
        pass

class HuaweiFirewallConnector(FirewallConnector):
    # 华为防火墙具体实现
    
class CiscoFirewallConnector(FirewallConnector):
    # 思科防火墙具体实现
```

### 6.2 策略类型扩展
- 基于策略类型字段，支持后续扩展不同VPN类型
- 策略配置采用JSON格式，支持灵活扩展策略参数

### 6.3 告警通知扩展
- 支持多种告警通知方式（系统内通知、邮件、短信等）
- 可扩展自定义告警处理流程 