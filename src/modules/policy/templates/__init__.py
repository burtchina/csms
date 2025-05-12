#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略模板管理模块

本模块负责管理策略相关的模板文件，提供以下功能：
1. 确保模板目录结构存在
2. 提供模板路径映射，明确每个视图函数使用的模板
3. 记录模板文件的用途和结构

模板目录结构:
- policy/          # 主模板目录
  - includes/      # 可复用的模板片段
  - modals/        # 模态框组件
  - alerts.html    # 告警列表页面
  - create.html    # 创建策略页面
  - deploy.html    # 部署策略页面  
  - detail.html    # 策略详情页面
  - edit.html      # 编辑策略页面
  - index.html     # 策略列表页面
  - template_list.html   # 模板列表页面

注意: 这些模板文件是模块内模板。全局模板路径为src/templates/policy/下的同名文件，
应确保只使用一套模板，避免重复维护导致的问题。
"""

import os
import logging

# 模板映射表 - 记录每个视图函数使用的模板文件
TEMPLATE_MAPPING = {
    # 视图函数名: 模板文件路径
    'index': 'policy/index.html',              # 策略列表页面
    'create': 'policy/create.html',            # 创建策略页面
    'detail': 'policy/detail.html',            # 策略详情页面
    'edit': 'policy/edit.html',                # 编辑策略页面
    'deploy': 'policy/deploy.html',            # 部署策略页面
    'template_list': 'policy/template_list.html',    # 模板列表页面
    'alerts': 'policy/alerts.html',            # 告警列表页面
}

# 模板注释表 - 记录每个模板文件的用途
TEMPLATE_DOCUMENTATION = {
    'policy/index.html': '策略列表页面 - 显示所有策略的列表，提供创建、编辑、删除和部署等操作入口',
    'policy/create.html': '创建策略页面 - 提供表单创建新的策略，支持从模板创建',
    'policy/detail.html': '策略详情页面 - 显示单个策略的详细信息，包括配置、部署记录和审计日志',
    'policy/edit.html': '编辑策略页面 - 修改现有策略的属性和配置',
    'policy/deploy.html': '部署策略页面 - 选择设备并部署策略，包含部署选项和结果展示',
    'policy/template_list.html': '模板列表页面 - 显示所有可用的策略模板',
    'policy/alerts.html': '告警列表页面 - 显示所有策略相关的告警记录',
    'policy/includes/': '包含可复用的模板片段，如表格、表单和卡片组件',
    'policy/modals/': '包含可复用的模态框组件，如确认对话框、预览框等',
}

# 全局标记防止重复创建模板目录
_template_directory_ensured = False

def ensure_template_directory():
    """
    确保策略模板目录结构存在
    
    创建模板目录及子目录(如果不存在)，记录创建过程，
    并返回创建结果。使用全局标记避免重复调用。
    
    Returns:
        bool: 目录创建/检查是否成功
    """
    global _template_directory_ensured
    
    # 如果已经确认过目录存在，直接返回成功
    if _template_directory_ensured:
        logging.debug("策略模板目录已经检查过，跳过重复检查")
        return True
    
    try:
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建模板目录(如果不存在)
        templates_dir = os.path.join(current_dir, 'policy')
        templates_dir_existed = os.path.exists(templates_dir)
        
        if not templates_dir_existed:
            os.makedirs(templates_dir)
            logging.info(f"创建策略模板目录: {templates_dir}")
        
        # 创建子目录
        is_new_dir_created = not templates_dir_existed
        subdirs = ['includes', 'modals']
        for subdir in subdirs:
            subdir_path = os.path.join(templates_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
                logging.info(f"创建策略模板子目录: {subdir_path}")
                is_new_dir_created = True
        
        # 创建空白的默认README文件，帮助开发者理解模板结构
        readme_path = os.path.join(templates_dir, 'README.md')
        if not os.path.exists(readme_path):
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("# 策略管理模块模板\n\n")
                f.write("本目录包含策略管理模块的模板文件。\n\n")
                f.write("## 模板文件列表及用途\n\n")
                for template, description in TEMPLATE_DOCUMENTATION.items():
                    f.write(f"- `{template}`: {description}\n")
                f.write("\n## 路由与模板映射\n\n")
                for view_func, template in TEMPLATE_MAPPING.items():
                    f.write(f"- `{view_func}()`: 使用 `{template}`\n")
            logging.info(f"创建模板目录README文件: {readme_path}")
            is_new_dir_created = True
        
        # 仅在有新目录创建时才记录总结日志
        if is_new_dir_created:
            logging.info("策略模板目录结构已创建/更新完成")
        else:
            logging.debug("策略模板目录结构已存在，无需创建")
        
        # 设置全局标记，避免重复检查
        _template_directory_ensured = True
                
        return True
    except Exception as e:
        logging.error(f"创建策略模板目录失败: {str(e)}")
        return False

def get_template_path(view_function_name):
    """
    获取视图函数对应的模板路径
    
    Args:
        view_function_name (str): 视图函数名称
        
    Returns:
        str: 对应的模板路径，如果不存在则返回None
    """
    return TEMPLATE_MAPPING.get(view_function_name)

def get_template_documentation(template_path):
    """
    获取模板文件的用途说明
    
    Args:
        template_path (str): 模板路径
        
    Returns:
        str: 模板的用途说明，如果不存在则返回None
    """
    return TEMPLATE_DOCUMENTATION.get(template_path) 