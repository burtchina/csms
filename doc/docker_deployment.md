# Docker部署指南

本文档详细介绍了如何使用Docker容器化技术部署校园安全管理系统(CSMS)。

## 前提条件

- 安装Docker (20.10.0+)
- 安装Docker Compose (2.0.0+)
- 基本的Docker和Linux命令知识

## 部署步骤

### 1. 准备环境

确保目标服务器已安装Docker和Docker Compose：

```bash
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version
```

### 2. 克隆代码仓库

```bash
git clone https://github.com/your-username/csms.git
cd csms
```

### 3. 配置环境变量

根据需要修改`docker-compose.yml`文件中的环境变量：

- 修改`SECRET_KEY`为一个随机安全的字符串
- 根据需要修改数据库凭证（用户名、密码）
- 调整其他环境配置如邮件服务器设置等

### 4. 创建必要的目录和文件

```bash
# 创建日志和数据目录
mkdir -p logs data
touch logs/.gitkeep data/.gitkeep
```

### 5. 构建并启动容器

```bash
# 构建和启动所有服务容器（后台运行）
docker-compose up -d

# 或者只构建不启动
# docker-compose build

# 查看容器状态
docker-compose ps
```

### 6. 初始化数据库

首次部署时，需要初始化数据库：

```bash
# 进入web容器
docker-compose exec web bash

# 执行数据库初始化命令
python src/init_db.py

# 或者使用Flask数据库迁移命令
# flask db init
# flask db migrate -m "initial migration"
# flask db upgrade

# 退出容器
exit
```

### 7. 访问系统

部署完成后，可以通过以下地址访问系统：

```
http://服务器IP:5000
```

## 常用操作命令

### 查看容器状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看web服务日志
docker-compose logs web

# 实时查看web服务日志
docker-compose logs -f web
```

### 启停服务

```bash
# 停止所有服务
docker-compose stop

# 启动所有服务
docker-compose start

# 重启特定服务
docker-compose restart web
```

### 更新应用程序

当代码有更新时，执行以下步骤更新应用：

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose up -d --build
```

### 数据备份与恢复

#### 备份数据库

```bash
# 备份MySQL数据库
docker-compose exec db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" csms' > backup_$(date +%Y%m%d).sql
```

#### 恢复数据库

```bash
# 恢复MySQL数据库
cat backup_20240701.sql | docker-compose exec -T db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" csms'
```

## 生产环境优化

### 安全性配置

1. 更改默认密码：修改docker-compose.yml中的默认密码
2. 限制端口暴露：仅暴露必要端口，考虑使用反向代理
3. 配置SSL/TLS：建议在生产环境使用HTTPS

### 性能优化

1. 调整Gunicorn工作进程数：根据服务器CPU核心数调整
2. 配置Redis缓存：优化会话和查询缓存
3. 配置数据库连接池：优化数据库连接管理

### 监控和日志

1. 配置日志收集：使用ELK或其他日志管理系统
2. 设置容器监控：使用Prometheus和Grafana监控系统性能
3. 配置告警机制：设置关键指标告警

## 故障排除

### 容器无法启动

检查日志查找错误：

```bash
docker-compose logs web
```

### 数据库连接问题

检查数据库连接配置和网络：

```bash
# 检查数据库是否正常运行
docker-compose ps db

# 进入容器测试数据库连接
docker-compose exec web python -c "from sqlalchemy import create_engine; engine = create_engine('mysql+pymysql://csms:csmspassword@db/csms'); connection = engine.connect(); print('连接成功')"
```

### 权限问题

检查挂载目录的权限：

```bash
# 确保data和logs目录有适当的权限
sudo chown -R 1000:1000 data logs
```

## 常见问题解答

**Q: 如何修改应用端口?**
A: 在docker-compose.yml文件中修改ports配置，例如从"5000:5000"改为"8080:5000"。

**Q: 如何使用外部MySQL数据库?**
A: 修改docker-compose.yml文件中的环境变量`SQLALCHEMY_DATABASE_URI`指向外部数据库，并移除db服务配置。

**Q: 如何扩展应用实例数量?**
A: 使用Docker Swarm或Kubernetes进行水平扩展，单机环境可使用`docker-compose up -d --scale web=3`启动多个web实例。 