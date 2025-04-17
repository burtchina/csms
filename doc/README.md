# 校园安全管理系统(CSMS)

## 项目简介

校园安全管理系统(CSMS)是一个专为学校安全管理部门设计的综合性网络应用平台，旨在提供全面的校园安全设备管理、监控和维护解决方案。系统集成了设备管理、故障诊断、维护调度、性能监控和数据分析等功能，为校园安全管理提供了强有力的信息化支持。

## 系统特点

- **模块化架构**：系统采用模块化设计，各功能模块相对独立，便于维护和扩展
- **响应式界面**：基于Bootstrap的响应式设计，适配各类终端设备
- **权限管理**：完善的用户角色和权限管理，确保数据安全
- **实时监控**：对校园安全设备进行实时状态监控和性能分析
- **故障诊断**：智能故障诊断和报警系统，提高故障处理效率
- **数据可视化**：直观的数据展示和分析功能，辅助决策

## 技术架构

- **前端技术**：HTML5, CSS3, JavaScript, Bootstrap 5.1.3
- **后端框架**：Flask 2.0.1
- **数据库**：SQLite (开发环境), MySQL (生产环境)
- **ORM框架**：SQLAlchemy 1.4.23
- **用户认证**：Flask-Login 0.5.0
- **表单处理**：Flask-WTF 1.0.0
- **网络通信**：Netmiko 3.4.0, Paramiko 2.8.0
- **任务调度**：Celery 5.2.7, APScheduler 3.8.0
- **数据缓存**：Redis 3.5.3

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
   flask db init
   flask db migrate -m "initial migration"
   flask db upgrade
   ```

6. 运行应用
   ```
   python src/app.py
   ```

7. 访问系统
   ```
   http://localhost:5000
   ```

## 项目文档

- [项目进度报告](project_progress.md)
- [API文档](api_docs.md) (待完成)
- [用户手册](user_manual.md) (待完成)
- [开发指南](dev_guide.md) (待完成)

## 默认账号

系统初始化后预设了以下账号用于测试：

1. 管理员账号
   - 用户名: `admin`
   - 密码: `admin123`

2. 测试用户账号
   - 用户名: `test`
   - 密码: `test123`

**注意**：生产环境部署前请务必修改默认密码。

## 项目团队

- 项目经理：XXX
- 后端开发：XXX
- 前端开发：XXX
- 测试：XXX
- 运维：XXX

## 许可协议

本项目采用 [MIT 许可协议](LICENSE)。 