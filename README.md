# 校园安全管理系统 (CSMS)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

校园安全管理系统（Campus Security Management System，简称CSMS）是一个基于Python开发的综合性网络设备监控和管理平台，旨在提高校园网络的安全性和可靠性。系统通过与eNSP（Enterprise Network Simulation Platform）集成，实时监控路由器、交换机等网络设备的状态信息，提供故障检测、性能监控和维护管理等功能。

## 项目文档

项目采用文档驱动开发模式，主要文档包括：

- [需求分析文档](doc/需求分析.md)：详细描述系统需求和功能
- [系统架构设计](doc/系统架构设计.md)：系统整体架构设计
- [网络设备接口设计](doc/网络设备接口设计.md)：与网络设备通信的接口设计
- [模块设计](doc/模块设计.md)：系统各模块的详细设计
- [项目规划](doc/项目规划.md)：项目开发计划和里程碑

## 系统功能

校园安全管理系统主要提供以下功能：

### 首页

- 系统概览：设备总数、在线设备数、故障设备数等关键指标
- 最近故障信息展示
- 待处理维护任务
- 性能异常设备列表

### 设备管理

- **设备列表**：展示所有网络设备基本信息和状态
- **本地设备监控**：实时监控设备状态和性能

### 故障管理

- **故障列表**：展示所有设备故障信息
- **故障上报**：支持手动上报故障和自动检测故障

### 维护管理

- **维护任务**：管理设备维护任务
- **维护日历**：可视化展示维护计划
- **创建任务**：创建新的维护任务
- **维护统计**：统计分析维护数据

### 性能管理

- **性能监控**：监控设备CPU、内存、带宽等关键指标
- **阈值设置**：设置性能指标阈值，超过阈值触发告警
- **性能报告**：生成设备性能报告

### 系统管理

- **用户管理**：管理系统用户和权限
- **账户密码管理**：管理用户账户和密码策略

## 技术架构

### 后端技术栈

- **编程语言**：Python 3.8+
- **Web框架**：Flask 2.0+
- **数据库**：MySQL 8.0
- **ORM框架**：SQLAlchemy
- **缓存**：Redis
- **设备通信**：Paramiko (SSH), PySNMP, Netmiko

### 前端技术栈

- **框架**：Bootstrap, jQuery
- **数据可视化**：ECharts
- **交互**：AJAX

## 项目结构

```
src/
├── app.py                 # 应用程序入口
├── config.py              # 配置文件
├── core/                  # 核心功能
│   ├── __init__.py
│   ├── db.py              # 数据库连接
│   ├── auth.py            # 认证逻辑
│   └── models.py          # 核心模型（已部分迁移）
├── models/                # 所有数据模型（新）
│   ├── __init__.py        # 导出所有模型
│   ├── base.py            # 基础模型类
│   ├── device.py          # 设备相关模型
│   └── performance.py     # 性能相关模型
├── modules/               # 功能模块
│   ├── __init__.py
│   ├── device/            # 设备管理模块
│   │   ├── __init__.py
│   │   ├── routes.py      # 路由
│   │   ├── services.py    # 业务逻辑
│   │   └── models.py      # 模型（已迁移到src/models）
│   ├── performance/       # 性能监控模块
│   └── maintenance/       # 维护管理模块
├── templates/             # HTML模板
└── static/                # 静态文件
```

## 代码重构说明

本项目进行了代码重构，将数据模型从各模块的models.py文件迁移到统一的models目录。主要变更如下：

1. 创建了统一的`src/models`目录存放所有数据模型
2. 新增`BaseModel`基类提供所有模型共享的功能
3. 将设备模型从`src/modules/device/models.py`迁移到`src/models/device.py`
4. 将性能记录模型从`src/core/models.py`迁移到`src/models/performance.py`
5. 原模块下的models.py文件保留为兼容层，通过导入新位置的模型保持向后兼容性

## 遵循的最佳实践

1. **关注点分离**：模型定义与业务逻辑分离
2. **单一职责原则**：每个模块负责一个功能领域
3. **避免循环导入**：通过集中模型定义避免循环引用
4. **统一导入路径**：提供一致的导入路径，即`from src.models import XXX`
5. **可扩展性**：易于添加新模块和功能

## 使用方法

使用新的导入路径:

```python
# 旧方式（不推荐，但仍然可用）
from src.modules.device.models import Device

# 新方式（推荐）
from src.models import Device
```

## 下一步重构计划

1. 将用户和角色模型迁移到`src/models/user.py`
2. 创建`src/models/maintenance.py`管理维护相关模型
3. 完善其他核心模型的迁移

## 安装与运行

### 前置条件

- Python 3.8+
- MySQL 8.0
- Redis

### 安装步骤

1. 克隆项目代码：

   ```bash
   git clone https://github.com/yourusername/csms.git
   cd csms
   ```

2. 创建并激活虚拟环境：

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. 安装项目依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 初始化数据库：

   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. 运行应用：

   ```bash
   flask run
   ```

### 配置说明

项目主要配置项包括：

- 数据库连接配置
- 设备通信配置
- 安全配置
- 邮件通知配置

详细配置说明请参考[配置文档](doc/配置说明.md)。

## 贡献指南

欢迎贡献代码或提交问题反馈。贡献前请先阅读[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 联系方式

- 项目维护者：[Your Name](mailto:your.email@example.com)
- 项目官网：[https://www.example.com/csms](https://www.example.com/csms)

## 主要功能

- **设备管理**：管理网络设备的基本信息、配置和状态
- **故障监控**：实时监控网络设备的故障和警告信息
- **性能分析**：收集和分析设备性能数据，如CPU使用率、内存占用等
- **安全审计**：记录系统操作日志，支持安全审计
- **用户管理**：管理系统用户，包括用户权限控制

## 更新日志

### 2025-04-20 更新

- **新增实时监控模块**：
  - 支持对网络设备进行实时性能监控，包括CPU使用率、内存使用率和接口流量
  - 根据设备类型自动选择合适的命令获取性能数据
  - 实现自动保活机制，避免SSH连接超时断开
  - 优化接口查询，减少对设备的访问频率
  - 支持性能阈值监控和告警功能
  - 提供实时性能数据图表展示

## 安装指南

1. 克隆代码库
```bash
git clone https://github.com/yourusername/csms.git
cd csms
```

2. 安装依赖包
```bash
# 安装基本依赖
pip install -r requirements.txt

# 安装监控功能所需依赖
python scripts/install_monitor_deps.py
```

3. 初始化数据库
```bash
python run.py --reset-db
```

4. 启动应用
```bash
python run.py
```

## 使用说明

详细使用说明请参考docs目录下的文档：

- [快速开始指南](docs/快速开始.md)
- [设备管理](docs/设备管理.md)
- [故障监控](docs/故障监控.md)
- [实时监控使用指南](docs/实时监控使用指南.md)
- [性能分析](docs/性能分析.md)
- [系统配置](docs/系统配置.md)

## 技术栈

- 后端：Python + Flask + SQLAlchemy
- 前端：Bootstrap + jQuery + Chart.js
- 数据库：SQLite（开发环境）/ MySQL（生产环境）
- 网络设备连接：Netmiko、Paramiko
- 安全性：Flask-Login、Werkzeug

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

该项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 联系方式

项目维护人 - admin@example.com 