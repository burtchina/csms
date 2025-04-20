# Git工作流程手册

## 基本提交流程

```bash
# 1. 查看修改状态
git status

# 2. 添加修改的文件
git add src/modules/device/templates/device/types.html src/modules/device/templates/device/edit_type.html

# 3. 提交修改（添加有意义的提交信息）
git commit -m "修复: 设备类型页面500错误，将len()替换为Jinja2的length过滤器"

# 4. 推送到远程仓库
git push origin main
```

## 完整版命令（包含更多选项）

```bash
# 1. 查看工作区状态
git status

# 2. 查看具体修改内容
git diff src/modules/device/templates/device/types.html
git diff src/modules/device/templates/device/edit_type.html

# 3. 暂存特定文件
git add src/modules/device/templates/device/types.html src/modules/device/templates/device/edit_type.html
# 或暂存所有修改
# git add .

# 4. 查看暂存区
git status

# 5. 提交修改（简短提交信息）
git commit -m "修复: 设备类型页面500错误，将len()替换为Jinja2的length过滤器"

# 或创建详细提交信息
# git commit
# 然后在编辑器中输入:
# 修复: 设备类型页面500错误
# 
# - 将templates/device/types.html中的len()替换为|length过滤器
# - 将templates/device/edit_type.html中进行同样修改
# - 解决了设备类型页面无法加载的问题

# 6. 确认提交
git show HEAD

# 7. 推送到远程仓库
git push origin main  # 替换main为您的分支名
```

## 分支操作（如需要）

```bash
# 创建并切换到新分支
git checkout -b bugfix/device-type-500-error

# 提交修改
git add src/modules/device/templates/device/types.html src/modules/device/templates/device/edit_type.html
git commit -m "修复: 设备类型页面500错误，将len()替换为Jinja2的length过滤器"

# 推送新分支到远程
git push -u origin bugfix/device-type-500-error

# 完成后合并到主分支
git checkout main
git merge bugfix/device-type-500-error
git push origin main

# 可选：删除bugfix分支
git branch -d bugfix/device-type-500-error
git push origin --delete bugfix/device-type-500-error
```

## 常见问题处理

```bash
# 如果推送被拒绝(远程有更新)
git pull --rebase origin main
git push origin main

# 如果有冲突
# 解决冲突后
git add .
git rebase --continue
git push origin main

# 如果需要撤销最后一次提交
git reset --soft HEAD~1
```

## 特定场景操作

### 修复线上紧急问题

```bash
# 1. 从主分支创建hotfix分支
git checkout main
git pull
git checkout -b hotfix/device-type-500-error

# 2. 在hotfix分支上修复问题
git add src/modules/device/templates/device/types.html
git commit -m "紧急修复: 设备类型页面500错误"

# 3. 推送修复并合并到主分支
git push -u origin hotfix/device-type-500-error
# (通过GitHub创建Pull Request并合并)

# 4. 同步本地主分支
git checkout main
git pull
```

### 特定版本标记

```bash
# 为当前提交创建标签
git tag -a v1.2.3 -m "版本1.2.3 - 修复设备类型页面错误"

# 推送标签到远程
git push origin v1.2.3

# 查看所有标签
git tag
```

## 提交信息规范

建议使用以下格式编写提交信息:

```
<类型>: <简短描述>

<详细描述>

<相关问题编号>
```

类型包括:
- `修复`: 修复bug
- `功能`: 新功能
- `文档`: 文档更新
- `样式`: 代码风格变更（不影响功能）
- `重构`: 代码重构（不影响功能）
- `性能`: 性能优化
- `测试`: 添加测试
- `构建`: 构建系统或外部依赖变更
- `其他`: 其它变更

示例:
```
修复: 设备类型页面500错误

- 将Jinja2模板中的len()函数替换为|length过滤器
- 修改了types.html和edit_type.html文件

问题: #123
``` 