# Windows本地部署指南

本文档详细介绍如何在Windows系统上从GitHub拉取校园安全管理系统(CSMS)代码，并在本地环境中运行系统。

## 1. 环境准备

在开始部署前，请确保您的Windows电脑已安装以下必要软件：

### 1.1 安装Git

1. 下载Git安装包
   - 访问[Git官方网站](https://git-scm.com/download/win)
   - 下载Windows版本的Git安装程序

2. 安装Git
   - 运行下载的安装程序
   - 大部分选项保持默认设置即可
   - 在"Adjusting your PATH environment"步骤，选择"Git from the command line and also from 3rd-party software"
   - 完成安装后，打开"命令提示符"或"PowerShell"，输入`git --version`确认安装成功

### 1.2 安装Python

1. 下载Python安装包
   - 访问[Python官方网站](https://www.python.org/downloads/windows/)
   - 下载Python 3.8+版本(推荐3.8.10)
   
2. 安装Python
   - 运行下载的安装程序
   - 勾选"Add Python to PATH"选项
   - 点击"Install Now"进行安装
   - 安装完成后，打开命令提示符，输入`python --version`和`pip --version`确认安装成功

### 1.3 安装MySQL(可选)

如果您打算使用MySQL数据库而非默认的SQLite数据库：

1. 下载MySQL安装包
   - 访问[MySQL官方网站](https://dev.mysql.com/downloads/installer/)
   - 下载MySQL Installer

2. 安装MySQL
   - 运行安装程序，选择"Custom"安装
   - 至少选择安装"MySQL Server"和"MySQL Workbench"
   - 按照向导设置root密码并完成安装

## 2. 拉取代码

### 2.1 克隆GitHub仓库

1. 打开命令提示符或PowerShell
2. 导航到您想要存放项目的目录，例如：
   ```bash
   cd D:\projects
   ```
3. 克隆代码仓库：
   ```bash
   git clone https://github.com/your-username/csms.git
   ```
   > 注意：请将链接中的"your-username"替换为实际的GitHub用户名或组织名

4. 进入项目目录：
   ```bash
   cd csms
   ```

## 3. 配置开发环境

### 3.1 创建虚拟环境

虚拟环境可以为项目提供独立的Python环境，避免依赖冲突：

1. 在项目根目录中创建虚拟环境：
   ```bash
   python -m venv venv
   ```

2. 激活虚拟环境：
   ```bash
   venv\Scripts\activate
   ```
   激活成功后，命令行前面会出现`(venv)`前缀

### 3.2 安装项目依赖

1. 更新pip：
   ```bash
   python -m pip install --upgrade pip
   ```

2. 使用项目提供的依赖安装脚本(推荐)：
   ```bash
   python src/install_dependencies.py
   ```
   
   或者直接通过requirements.txt安装：
   ```bash
   pip install -r requirements.txt
   ```

3. 如果在安装过程中遇到PYSNMP相关依赖问题，可以尝试修复：
   ```bash
   python fix_dependencies.py
   ```

## 4. 初始化数据库

### 4.1 配置数据库连接

1. 默认情况下，系统使用SQLite数据库，无需额外配置

2. 如果需要使用MySQL，请修改`src/config.py`文件中的数据库连接配置：
   ```python
   # 找到DevelopmentConfig类中的SQLALCHEMY_DATABASE_URI设置，修改为：
   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://用户名:密码@localhost/csms'
   ```
   请将"用户名"和"密码"替换为您的MySQL用户名和密码

### 4.2 创建并初始化数据库

1. 执行数据库初始化脚本：
   ```bash
   python src/init_db.py
   ```
   
   此脚本会创建必要的数据库表并初始化系统所需的基础数据。
   首次运行时，系统会创建以下账号：
   - 管理员账号：admin / admin123
   - 测试账号：test / test123

## 5. 运行应用

### 5.1 设置环境变量

在Windows命令提示符中：
```bash
set FLASK_ENV=development
```

或在PowerShell中：
```powershell
$env:FLASK_ENV = "development"
```

### 5.2 启动应用

使用项目的启动脚本运行应用：
```bash
python run.py
```

或者带参数运行：
```bash
python run.py --port 5000 --host 127.0.0.1 --debug
```

### 5.3 访问系统

打开Web浏览器，访问：
```
http://localhost:5000
```

使用以下账号登录：
- 管理员账号：admin / admin123
- 测试账号：test / test123

## 6. 常见问题解决

### 6.1 依赖安装问题

**问题描述**：安装PySNMP相关依赖时出现错误。

**解决方案**：
```bash
# 安装特定版本的依赖
pip install pyasn1==0.4.8
pip install pysmi==0.3.4
pip install pycryptodomex==3.10.1
pip install pysnmp==4.4.12
```

### 6.2 数据库连接问题

**问题描述**：无法连接到MySQL数据库。

**解决方案**：
- 确认MySQL服务已启动
- 检查数据库用户名和密码是否正确
- 确认已创建名为"csms"的数据库

```bash
# 创建数据库的MySQL命令
CREATE DATABASE csms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6.3 端口占用问题

**问题描述**：启动应用时提示端口5000已被占用。

**解决方案**：
```bash
# 使用不同端口启动应用
python run.py --port 5001
```

然后访问 http://localhost:5001

### 6.4 访问权限问题

**问题描述**：在Windows上运行时，可能会遇到文件访问权限不足的问题。

**解决方案**：
- 以管理员身份运行命令提示符或PowerShell
- 确保项目目录具有足够的读写权限

## 7. 开发操作指南

### 7.1 代码结构

项目主要目录结构：
- `src/` - 源代码目录
  - `modules/` - 功能模块
  - `core/` - 核心功能和工具
  - `static/` - 静态资源
  - `templates/` - HTML模板
- `data/` - 数据文件目录
- `logs/` - 日志文件目录
- `doc/` - 文档目录

### 7.2 更新代码

当需要获取远程仓库的最新代码时：

```bash
# 确保在项目根目录下
git pull

# 如果有新的依赖，重新安装
python src/install_dependencies.py

# 如果有数据库结构变更，更新数据库
python src/init_db.py
```

### 7.3 使用Git进行代码管理

基本Git操作流程：

```bash
# 查看代码状态
git status

# 添加修改
git add .

# 提交修改
git commit -m "描述你的修改"

# 推送到远程仓库
git push origin main
```

更详细的Git使用指南请参考项目中的[Git工作流程手册](git_workflow.md)。

## 8. 参考资料

- [Python官方文档](https://docs.python.org/zh-cn/3.8/)
- [Flask官方文档](https://flask.palletsprojects.com/)
- [Git官方文档](https://git-scm.com/doc)
- 项目文档目录：`doc/` 