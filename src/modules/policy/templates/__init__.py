#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略模板管理模块
"""

import os
import logging

def ensure_template_directory():
    """确保策略模板目录存在"""
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
        
        # 仅在有新目录创建时才记录总结日志
        if is_new_dir_created:
            logging.info("策略模板目录结构已创建/更新完成")
        else:
            logging.debug("策略模板目录结构已存在，无需创建")
                
        return True
    except Exception as e:
        logging.error(f"创建策略模板目录失败: {str(e)}")
        return False 