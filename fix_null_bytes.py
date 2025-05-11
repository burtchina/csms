#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
扫描并修复文件中的空字节
"""

import os
import sys

def fix_null_bytes(file_path):
    """扫描文件中的空字节并修复它们"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        if b'\x00' in content:
            print(f"发现空字节: {file_path}")
            # 移除空字节
            fixed_content = content.replace(b'\x00', b'')
            
            # 创建备份
            backup_path = file_path + '.bak'
            with open(backup_path, 'wb') as f:
                f.write(content)
            print(f"已创建备份: {backup_path}")
            
            # 写入修复后的内容
            with open(file_path, 'wb') as f:
                f.write(fixed_content)
            print(f"已修复文件: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return False

def scan_directory(directory):
    """扫描目录中的所有Python文件"""
    fixed_files = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_null_bytes(file_path):
                    fixed_files += 1
    
    return fixed_files

if __name__ == "__main__":
    target_dir = "src"
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    
    print(f"开始扫描目录: {target_dir}")
    fixed_count = scan_directory(target_dir)
    print(f"扫描完成，修复了 {fixed_count} 个文件") 