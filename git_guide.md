# GitHub代码提交指南

## 前期准备

### 1. 安装Git

- **Windows**: 从[Git官网](https://git-scm.com/download/win)下载安装包
- **Mac**: 
  ```
  brew install git
  ```
- **Linux**: 
  ```
  sudo apt-get install git  # Ubuntu/Debian
  sudo yum install git      # CentOS/RHEL
  ```

### 2. 创建GitHub账户

访问[GitHub官网](https://github.com/)注册一个账户。

### 3. 配置Git

```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱"
```

## 基本操作流程

### 1. 创建/克隆仓库

**创建新仓库**:
1. 在GitHub网站上点击"New repository"
2. 填写仓库名称和描述
3. 选择是否初始化README文件
4. 点击"Create repository"

**克隆现有仓库**:
```bash
git clone https://github.com/用户名/仓库名.git
```

### 2. 基本工作流程

```bash
# 1. 查看当前状态
git status

# 2. 添加文件到暂存区
git add 文件名        # 添加指定文件
git add .            # 添加所有文件

# 3. 提交到本地仓库
git commit -m "提交说明"

# 4. 推送到GitHub
git push origin 分支名
```

### 3. 分支管理

```bash
# 查看所有分支
git branch

# 创建新分支
git branch 分支名

# 切换分支
git checkout 分支名

# 创建并切换到新分支
git checkout -b 分支名

# 合并分支到当前分支
git merge 分支名
```

### 4. 更新本地仓库

```bash
# 获取远程更新但不合并
git fetch

# 获取远程更新并合并到当前分支
git pull origin 分支名
```

## 常见工作场景

### 提交代码的完整流程

```bash
# 1. 确保你在正确的分支上
git branch

# 2. 获取最新代码
git pull origin 分支名

# 3. 创建并切换到新的功能分支（推荐）
git checkout -b feature/新功能名

# 4. 编写代码...

# 5. 查看更改
git status
git diff

# 6. 添加更改到暂存区
git add .

# 7. 提交更改
git commit -m "实现了xxx功能"

# 8. 推送到GitHub
git push origin feature/新功能名

# 9. 在GitHub上创建Pull Request
# 10. 代码审核后合并到主分支
```

### 解决合并冲突

当Git无法自动合并时会产生冲突：

1. 打开冲突文件，会看到类似以下标记：
   ```
   <<<<<<< HEAD
   当前分支的内容
   =======
   其他分支的内容
   >>>>>>> 分支名
   ```

2. 编辑文件解决冲突，删除标记符号
3. 添加修改后的文件：`git add 文件名`
4. 完成合并提交：`git commit -m "解决冲突"`

## 实用技巧

### 1. .gitignore文件

创建`.gitignore`文件，列出不想被Git跟踪的文件：

```
# 编译生成的文件
*.class
*.o
*.pyc

# 日志文件
*.log

# 系统文件
.DS_Store
Thumbs.db

# 依赖目录
/node_modules/
/venv/
```

### 2. 撤销操作

```bash
# 撤销工作区修改
git checkout -- 文件名

# 撤销暂存区修改
git reset HEAD 文件名

# 撤销最近一次提交
git reset --soft HEAD~1
```

### 3. 查看历史

```bash
# 查看提交历史
git log

# 查看简洁历史
git log --oneline

# 查看分支图
git log --graph --oneline --all
```

## 进阶使用

### 1. 使用SSH连接GitHub

1. 生成SSH密钥：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "你的邮箱"
   ```

2. 将公钥添加到GitHub：
   - 复制`~/.ssh/id_rsa.pub`文件内容
   - 在GitHub设置中添加SSH密钥

3. 测试连接：
   ```bash
   ssh -T git@github.com
   ```

### 2. 使用GitHub Desktop

如果不习惯命令行，可以使用[GitHub Desktop](https://desktop.github.com/)图形界面工具。

## 常见问题

1. **推送被拒绝**：可能是远程仓库有更新，先`git pull`再推送
2. **文件太大**：GitHub限制单个文件不超过100MB，使用Git LFS管理大文件
3. **提交信息写错**：使用`git commit --amend`修改最近的提交信息

## 参考资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub帮助文档](https://docs.github.com/cn)
- [GitLab中文文档](https://docs.gitlab.cn/) 