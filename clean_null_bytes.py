#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理文件中的空字节
"""

import os

def clean_file(filepath):
    """清理文件中的空字节
    
    Args:
        filepath: 文件路径
    """
    try:
        print(f"正在处理文件: {filepath}")
        # 读取文件内容
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # 检查是否包含空字节
        if b'\x00' in content:
            print(f"  发现空字节，正在清理: {filepath}")
            # 移除空字节
            cleaned_content = content.replace(b'\x00', b'')
            
            # 写回文件
            with open(filepath, 'wb') as f:
                f.write(cleaned_content)
            print(f"  文件清理完成: {filepath}")
        else:
            print(f"  文件不包含空字节: {filepath}")
    except Exception as e:
        print(f"  处理文件时出错: {e}")

def clean_directory(dirpath):
    """清理目录中所有Python文件的空字节
    
    Args:
        dirpath: 目录路径
    """
    print(f"正在处理目录: {dirpath}")
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                clean_file(filepath)

if __name__ == "__main__":
    # 清理auth服务模块
    clean_directory('src/modules/auth/services')
    
    # 清理policy模块
    clean_directory('src/modules/policy')
    
    print("所有文件处理完成") 