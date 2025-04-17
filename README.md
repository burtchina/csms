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
csms/
├── doc/                    # 项目文档
├── src/                    # 源代码
│   ├── core/               # 核心模块
│   ├── modules/            # 业务模块
│   ├── static/             # 静态资源
│   ├── templates/          # 模板文件
│   ├── app.py              # 应用入口
│   └── config.py           # 配置文件
├── tests/                  # 测试代码
├── requirements.txt        # 项目依赖
└── README.md               # 项目说明
```

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