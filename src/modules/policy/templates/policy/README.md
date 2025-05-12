# 策略管理模块模板

本目录包含策略管理模块的模板文件。

## 模板文件列表及用途

- `policy/index.html`: 策略列表页面 - 显示所有策略的列表，提供创建、编辑、删除和部署等操作入口
- `policy/create.html`: 创建策略页面 - 提供表单创建新的策略，支持从模板创建
- `policy/detail.html`: 策略详情页面 - 显示单个策略的详细信息，包括配置、部署记录和审计日志
- `policy/edit.html`: 编辑策略页面 - 修改现有策略的属性和配置
- `policy/deploy.html`: 部署策略页面 - 选择设备并部署策略，包含部署选项和结果展示
- `policy/template_list.html`: 模板列表页面 - 显示所有可用的策略模板
- `policy/alerts.html`: 告警列表页面 - 显示所有策略相关的告警记录
- `policy/includes/`: 包含可复用的模板片段，如表格、表单和卡片组件
- `policy/modals/`: 包含可复用的模态框组件，如确认对话框、预览框等

## 路由与模板映射

- `index()`: 使用 `policy/index.html`
- `create()`: 使用 `policy/create.html`
- `detail()`: 使用 `policy/detail.html`
- `edit()`: 使用 `policy/edit.html`
- `deploy()`: 使用 `policy/deploy.html`
- `template_list()`: 使用 `policy/template_list.html`
- `alerts()`: 使用 `policy/alerts.html`
