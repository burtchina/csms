# Docker容器化部署指南

本文档详细介绍了如何使用Docker容器化技术部署校园安全管理系统(CSMS)。通过容器化部署，可以简化安装过程、提高系统可移植性并实现更灵活的扩展。

## 1. 部署架构

CSMS系统采用以下容器组件构成完整的部署架构：

- **Web应用容器**：运行Flask应用程序，处理HTTP请求
- **Celery工作容器**：处理异步任务，如设备监控和报告生成
- **MySQL数据库容器**：存储系统数据
- **Redis缓存容器**：提供缓存和消息队列服务
- **Nginx容器**：提供反向代理、SSL终止和静态资源服务

![Docker部署架构](../static/img/docker_architecture.png)

## 2. 前提条件

在部署前，确保您的服务器满足以下条件：

- 安装Docker (20.10.0+)
- 安装Docker Compose (2.0.0+)
- 至少2GB RAM和10GB硬盘空间
- 对外网络连接（用于拉取Docker镜像）
- 基本的Linux命令行操作知识

## 3. 部署前准备

### 3.1 安装Docker和Docker Compose

如果您的服务器尚未安装Docker，请按照以下步骤安装：

```bash
# 更新软件包索引
sudo apt update

# 安装必要的依赖
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 添加Docker仓库
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 更新软件包索引
sudo apt update

# 安装Docker CE
sudo apt install -y docker-ce

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3.2 验证Docker安装

```bash
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version

# 运行测试容器
docker run --rm hello-world
```

## 4. 部署步骤

### 4.1 获取项目代码

```bash
# 克隆仓库
git clone https://github.com/your-username/csms.git
cd csms
```

### 4.2 配置环境

项目包含以下关键配置文件：

- `Dockerfile`：定义应用容器
- `docker-compose.yml`：定义多容器部署配置
- `nginx/csms.conf`：Nginx配置
- `config/production.py`：生产环境应用配置

在部署前需要调整以下配置：

1. 修改`docker-compose.yml`中的环境变量，特别是：
   - `SECRET_KEY`：修改为随机字符串
   - 数据库凭证：根据需要修改用户名和密码
   - 邮件服务配置：根据您的邮件服务器设置

2. 修改`nginx/csms.conf`中的域名：
   - 将`csms.example.com`替换为您的实际域名

### 4.3 创建必要的目录结构

```bash
# 创建目录结构
mkdir -p logs data nginx/ssl static

# 设置适当的权限
chmod -R 755 logs data nginx static
```

### 4.4 配置SSL证书（生产环境）

对于生产环境，强烈建议配置SSL证书：

```bash
# 将您的SSL证书和密钥放置在nginx/ssl目录中
cp your-certificate.crt nginx/ssl/csms.crt
cp your-private-key.key nginx/ssl/csms.key

# 确保证书权限正确
chmod 644 nginx/ssl/csms.crt
chmod 600 nginx/ssl/csms.key
```

如果您没有SSL证书，可以使用Let's Encrypt免费获取：

```bash
# 安装certbot
sudo apt install -y certbot

# 获取证书
sudo certbot certonly --standalone -d csms.example.com

# 复制证书到nginx/ssl目录
sudo cp /etc/letsencrypt/live/csms.example.com/fullchain.pem nginx/ssl/csms.crt
sudo cp /etc/letsencrypt/live/csms.example.com/privkey.pem nginx/ssl/csms.key
```

### 4.5 构建和启动容器

```bash
# 构建和启动所有服务（后台运行）
docker-compose up -d

# 检查容器状态
docker-compose ps
```

### 4.6 初始化数据库

首次部署需要初始化数据库：

```bash
# 进入Web容器
docker-compose exec web bash

# 执行数据库初始化
python src/init_db.py

# 或使用Flask迁移命令
# flask db init
# flask db migrate -m "初始化数据库"
# flask db upgrade

# 退出容器
exit
```

### 4.7 验证部署

通过以下URL访问系统：

- 开发/测试环境：`http://服务器IP:5000`
- 生产环境：`https://您的域名`

## 5. 日常运维操作

### 5.1 查看容器状态和日志

```bash
# 查看所有容器状态
docker-compose ps

# 查看Web应用日志
docker-compose logs web

# 实时跟踪日志
docker-compose logs -f web

# 查看特定数量的日志行
docker-compose logs --tail=100 web
```

### 5.2 启停服务

```bash
# 停止所有服务
docker-compose stop

# 启动所有服务
docker-compose start

# 重启特定服务
docker-compose restart web

# 完全关闭并移除容器
docker-compose down
```

### 5.3 更新应用

当有代码更新时：

```bash
# 拉取最新代码
git pull

# 重新构建并启动容器
docker-compose up -d --build
```

### 5.4 数据备份与恢复

定期备份数据库是系统维护的重要部分：

```bash
# 备份MySQL数据库
docker-compose exec db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" csms' > backup_$(date +%Y%m%d).sql

# 恢复数据库备份
cat backup_20240701.sql | docker-compose exec -T db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" csms'
```

建议设置自动备份脚本：

```bash
#!/bin/bash
# 文件名: backup_db.sh

# 备份目录
BACKUP_DIR="/path/to/backups"
mkdir -p $BACKUP_DIR

# 备份文件名
BACKUP_FILE="$BACKUP_DIR/csms_$(date +\%Y\%m\%d_\%H\%M\%S).sql"

# 执行备份
docker-compose exec -T db sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" csms' > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 保留最近30天的备份
find $BACKUP_DIR -name "csms_*.sql.gz" -type f -mtime +30 -delete
```

将此脚本添加到crontab执行定期备份：

```bash
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup_db.sh >> /var/log/db_backup.log 2>&1
```

## 6. 性能优化

### 6.1 Gunicorn配置优化

修改`Dockerfile`中的启动命令可以优化Web服务器性能：

```dockerfile
# 根据CPU核心数调整workers数量
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "60", "run:app"]
```

推荐配置：
- `workers`：设置为CPU核心数 × 2 + 1
- `worker-class`：使用gevent提供异步支持
- `worker-connections`：根据内存调整连接数
- `timeout`：根据应用复杂性调整超时时间

### 6.2 Nginx性能优化

编辑`nginx/csms.conf`添加以下优化配置：

```nginx
# 配置Gzip压缩
gzip on;
gzip_comp_level 5;
gzip_min_length 256;
gzip_proxied any;
gzip_types
  application/javascript
  application/json
  application/xml
  text/css
  text/plain
  text/xml;

# 配置浏览器缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, no-transform";
}

# 调整连接参数
keepalive_timeout 65;
keepalive_requests 100;
```

### 6.3 数据库优化

对于生产环境，可以调整MySQL配置提高性能：

```yaml
# 在docker-compose.yml中为MySQL服务添加自定义配置
db:
  volumes:
    - mysql-data:/var/lib/mysql
    - ./mysql/my.cnf:/etc/mysql/conf.d/custom.cnf
```

创建`mysql/my.cnf`文件：

```ini
[mysqld]
# 增加缓冲池大小（根据可用内存调整）
innodb_buffer_pool_size = 512M

# 优化事务和日志设置
innodb_flush_log_at_trx_commit = 2
innodb_log_buffer_size = 16M

# 查询缓存
query_cache_size = 32M
query_cache_limit = 1M

# 连接数设置
max_connections = 300
```

## 7. 高可用部署（可选）

对于需要高可用性的生产环境，可以考虑以下方案：

### 7.1 使用Docker Swarm或Kubernetes

将`docker-compose.yml`转换为Docker Swarm或Kubernetes配置，实现容器编排和自动故障恢复。

### 7.2 数据库高可用

配置MySQL主从复制或使用云数据库服务，确保数据库高可用性。

### 7.3 负载均衡

在Nginx前添加负载均衡器，如HAProxy或云服务商提供的负载均衡服务。

## 8. 故障排除

### 8.1 容器启动问题

如果容器无法正常启动：

```bash
# 查看容器详细日志
docker-compose logs web

# 以交互模式运行容器检查问题
docker-compose run --rm web bash
```

### 8.2 数据库连接问题

如果应用无法连接数据库：

```bash
# 检查数据库容器状态
docker-compose ps db
docker-compose logs db

# 测试数据库连接
docker-compose exec web python -c "from sqlalchemy import create_engine; engine = create_engine('mysql+pymysql://csms:csmspassword@db/csms'); connection = engine.connect(); print('连接成功')"
```

### 8.3 Nginx配置问题

如果Nginx代理不正常：

```bash
# 检查Nginx配置语法
docker-compose exec nginx nginx -t

# 查看Nginx日志
docker-compose logs nginx
```

## 9. 安全考虑

### 9.1 环境变量管理

对于生产环境，建议使用环境变量文件管理敏感信息：

```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件设置密码和密钥
```

修改`docker-compose.yml`使用环境变量文件：

```yaml
services:
  web:
    env_file:
      - .env
```

### 9.2 容器安全最佳实践

- 定期更新基础镜像
- 使用非root用户运行容器
- 限制容器资源使用
- 实施网络隔离

### 9.3 定期安全更新

```bash
# 拉取最新的基础镜像
docker pull python:3.8-slim
docker pull nginx:1.21-alpine
docker pull mysql:8.0
docker pull redis:6.2-alpine

# 重新构建应用
docker-compose build --no-cache
docker-compose up -d
```

## 10. 常见问题与解答

**Q: 如何修改应用的访问端口?**  
A: 在`docker-compose.yml`中修改Nginx服务的ports配置，例如从"80:80"改为"8080:80"。

**Q: 如何使用外部数据库而不是容器数据库?**  
A: 修改`docker-compose.yml`中web服务的环境变量`SQLALCHEMY_DATABASE_URI`指向外部数据库，并移除db服务配置。

**Q: 如何扩展应用实例提高并发能力?**  
A: 使用Docker Swarm或Kubernetes进行水平扩展；单机环境可使用`docker-compose up -d --scale web=3`启动多个web实例，并调整Nginx配置实现负载均衡。

**Q: 如何实现自动化部署?**  
A: 结合CI/CD工具（如Jenkins、GitLab CI或GitHub Actions）实现代码提交后自动构建、测试和部署。 