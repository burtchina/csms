#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复表定义冲突脚本
在所有数据库模型类上添加 extend_existing=True 选项
"""

import os
import sys
import re
from typing import List, Dict, Any, Tuple

# 获取项目根目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

def find_model_files() -> List[str]:
    """查找所有可能包含模型定义的文件"""
    model_files = []
    
    # 遍历源代码目录
    for root, dirs, files in os.walk(os.path.join(base_dir, "src")):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 查找类定义和db.Model
                    if "db.Model" in content and "class " in content:
                        model_files.append(file_path)
    
    return model_files

def fix_model_file(file_path: str) -> Tuple[bool, List[str]]:
    """修复模型文件中的表定义问题"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 使用正则表达式匹配模型类定义
    pattern = r"class\s+(\w+)\s*\(\s*db\.Model.*?\):"
    models_found = re.findall(pattern, content, re.DOTALL)
    
    # 如果没有找到模型类，跳过
    if not models_found:
        return False, []
    
    # 记录修改的模型类
    fixed_models = []
    modified = False
    
    for model_name in models_found:
        # 查找是否已定义 __table_args__
        table_args_pattern = r"class\s+" + re.escape(model_name) + r"\s*\(\s*db\.Model.*?\):.*?__table_args__\s*="
        has_table_args = re.search(table_args_pattern, content, re.DOTALL)
        
        # 如果没有定义 __table_args__，添加它
        if not has_table_args:
            # 找到类定义的结束位置
            class_def_pattern = r"class\s+" + re.escape(model_name) + r"\s*\(\s*db\.Model.*?\):"
            match = re.search(class_def_pattern, content, re.DOTALL)
            if match:
                # 在类定义后添加 __table_args__
                insert_point = match.end()
                new_content = content[:insert_point] + "\n    __table_args__ = {'extend_existing': True}" + content[insert_point:]
                content = new_content
                fixed_models.append(model_name)
                modified = True
        else:
            # 已有 __table_args__，检查是否包含 extend_existing
            extend_existing_pattern = r"__table_args__\s*=.*?extend_existing.*?}"
            has_extend_existing = re.search(extend_existing_pattern, content, re.DOTALL)
            
            if not has_extend_existing:
                # 找到 __table_args__ 定义
                table_args_def_pattern = r"(__table_args__\s*=\s*\{.*?\})"
                table_args_match = re.search(table_args_def_pattern, content, re.DOTALL)
                if table_args_match:
                    table_args_str = table_args_match.group(1)
                    # 在 __table_args__ 中添加 extend_existing=True
                    if table_args_str.strip().endswith("}"):
                        # 在右花括号前添加
                        new_table_args = table_args_str.replace("}", ", 'extend_existing': True}")
                        content = content.replace(table_args_str, new_table_args)
                        fixed_models.append(model_name)
                        modified = True
    
    # 如果有修改，写回文件
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    return modified, fixed_models

def main():
    """主函数"""
    print("开始修复表定义问题...")
    
    # 查找所有可能包含模型定义的文件
    model_files = find_model_files()
    print(f"找到 {len(model_files)} 个可能包含模型定义的文件")
    
    # 修复每个文件
    fixed_files = 0
    fixed_models_count = 0
    fixed_models_list = []
    
    for file_path in model_files:
        modified, fixed_models = fix_model_file(file_path)
        if modified:
            fixed_files += 1
            fixed_models_count += len(fixed_models)
            
            # 显示修复详情
            rel_path = os.path.relpath(file_path, base_dir)
            print(f"修复文件: {rel_path}")
            for model in fixed_models:
                print(f"  - 添加 extend_existing=True 到模型: {model}")
                fixed_models_list.append(f"{model} ({rel_path})")
    
    # 打印统计信息
    print("\n修复完成!")
    print(f"修复了 {fixed_files} 个文件中的 {fixed_models_count} 个模型类")
    
    if fixed_models_list:
        print("\n修复的模型类:")
        for model in fixed_models_list:
            print(f"  - {model}")
    
    print("\n如果问题仍然存在，请尝试手动修复数据库模型定义")

if __name__ == "__main__":
    main() 