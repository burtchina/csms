# 校园安全管理系统(CSMS)

## 项目简介

校园安全管理系统(CSMS)是一个专为学校安全管理部门设计的综合性网络应用平台，旨在提供全面的校园安全设备管理、监控和维护解决方案。系统集成了设备管理、故障诊断、维护调度、性能监控和数据分析等功能，为校园安全管理提供了强有力的信息化支持。

## 系统特点

- **模块化架构**：系统采用模块化设计，各功能模块相对独立，便于维护和扩展
- **响应式界面**：基于Bootstrap的现代化响应式设计，支持多端设备访问
- **权限管理**：完善的用户角色和权限管理，基于RBAC模型确保数据安全
- **实时监控**：对网络设备进行实时状态监控和性能分析，支持SNMP/SSH/Telnet多种协议
- **故障诊断**：智能故障诊断和告警系统，支持阈值设置和自动通知
- **数据可视化**：集成ECharts图表库，提供直观的数据展示和分析功能
- **维护管理**：完整的设备维护计划和任务分配流程管理

## 技术架构

- **前端技术**：HTML5, CSS3, JavaScript, Bootstrap 5.1.3, ECharts 5.3.1
- **后端框架**：Flask 2.0.1, Flask-RESTful 0.3.9
- **数据库**：SQLite (开发环境), MySQL 8.0 (生产环境)
- **ORM框架**：SQLAlchemy 1.4.23, Flask-SQLAlchemy 2.5.1
- **用户认证**：Flask-Login 0.5.0, JWT认证
- **表单处理**：Flask-WTF 1.0.0, WTForms 2.3.3
- **网络通信**：Netmiko 3.4.0/4.1.2, Paramiko 2.8.0/2.11.0, PySNMP 4.4.12
- **任务调度**：Celery 5.2.7, APScheduler 3.8.0
- **数据缓存**：Redis 3.5.3
- **数据分析**：Pandas 1.3.3, NumPy 1.21.2
- **测试工具**：Pytest 6.2.5, Pytest-Flask 1.2.0

## 安装与配置

### 环境要求

- Python 3.8+
- Redis 服务器 (用于缓存和任务队列)
- SQLite/MySQL 数据库

### 安装步骤

1. 克隆代码仓库
   ```
   git clone https://github.com/your-username/csms.git
   cd csms
   ```

2. 创建并激活虚拟环境
   ```
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 安装依赖包
   ```
   python src/install_dependencies.py
   # 或者直接使用
   pip install -r requirements.txt
   ```

4. 环境配置
   ```
   # 开发环境
   set FLASK_ENV=development
   # 生产环境
   set FLASK_ENV=production
   ```

5. 初始化数据库
   ```
   python src/init_db.py
   # 或者使用
   flask db init
   flask db migrate -m "initial migration"
   flask db upgrade
   ```

6. 运行应用
   ```
   python run.py
   # 可添加参数
   python run.py --port 5000 --host 0.0.0.0 --debug
   ```

7. 访问系统
   ```
   http://localhost:5000
   ```

## 项目文档

- [项目进度报告](project_progress.md)
- [API文档](api_docs.md)
- [用户手册](user_manual.md)
- [数据持久化方案](data_persistence_plan.md)
- [Git工作流程手册](git_workflow.md)
- [网络设备接口设计](网络设备接口设计.md)
- [系统架构设计](系统架构设计.md)
- [模块设计](模块设计.md)

## 系统功能模块

- **用户认证模块**：用户登录、注册、密码重置、权限管理
- **设备管理模块**：设备信息管理、设备状态监控、设备配置管理
- **故障管理模块**：故障检测、记录、告警与处理
- **维护管理模块**：维护计划、任务分配、维护记录
- **性能管理模块**：性能数据采集、阈值监控、报告生成
- **系统管理模块**：用户管理、系统配置、日志管理

## 默认账号

系统初始化后预设了以下账号用于测试：

1. 管理员账号
   - 用户名: `admin`
   - 密码: `admin123`
   - 权限: 系统管理员

2. 测试用户账号
   - 用户名: `test`
   - 密码: `test123`
   - 权限: 普通用户

**注意**：生产环境部署前请务必修改默认密码。

## 项目目录结构

```
csms/
├── data/                  # 数据库文件存储目录
├── doc/                   # 项目文档目录
├── logs/                  # 日志文件存储目录
├── requirements.txt       # 项目依赖
├── run.py                 # 应用启动脚本
├── scripts/               # 实用脚本工具
└── src/                   # 源代码目录
    ├── app.py             # 应用程序入口
    ├── config.py          # 配置文件
    ├── api.py             # API接口定义
    ├── core/              # 核心功能模块
    ├── models/            # 数据模型
    ├── modules/           # 功能模块
    │   ├── auth/          # 认证模块
    │   ├── device/        # 设备管理模块
    │   ├── fault/         # 故障管理模块
    │   ├── maintenance/   # 维护管理模块
    │   ├── performance/   # 性能监控模块
    │   └── system/        # 系统设置模块
    ├── static/            # 静态资源
    │   ├── css/           # CSS样式文件
    │   ├── js/            # JavaScript文件
    │   └── img/           # 图片资源
    └── templates/         # HTML模板
```

## 项目团队

- 项目经理：张三
- 后端开发：李四、王五
- 前端开发：赵六
- 测试：孙七
- 运维：周八

## 许可协议

本项目采用 [MIT 许可协议](LICENSE)。

## 常见问题解决(FAQ)

### 1. 设备类型页面出现500错误

**问题描述**：访问设备类型页面(`/device/types`)时出现500服务器内部错误。

**原因**：在Jinja2模板中错误使用了Python内置的`len()`函数获取集合长度。

**解决方案**：
- 在Jinja2模板中，应使用`|length`过滤器而非`len()`函数获取集合长度
- 示例：将`{{ len(devices) }}`修改为`{{ devices|length }}`

### 2. 依赖安装失败问题

**问题描述**：安装PySNMP依赖时出现版本冲突。

**原因**：PySNMP 4.4.12对特定版本的pyasn1有依赖要求。

**解决方案**：
- 使用提供的安装脚本按特定顺序安装依赖：`python src/install_dependencies.py`
- 或者手动按顺序安装：先安装pyasn1==0.4.8，再安装pysnmp==4.4.12

### 3. 无法连接设备问题

**问题描述**：系统无法连接到网络设备。

**原因**：设备凭证错误或网络不通。

**解决方案**：
- 检查设备的IP地址、用户名和密码是否正确
- 确保系统可以ping通设备
- 检查设备的SSH/Telnet/SNMP服务是否开启
- 查阅`doc/网络设备接口设计.md`文档获取详细信息 