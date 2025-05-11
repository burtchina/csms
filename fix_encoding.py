#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复文件编码问题，包括空字节和非UTF-8字符
"""

import os
import sys
import codecs
import re

def is_valid_python_content(content):
    """检查内容是否是有效的Python代码"""
    # 常见的Python代码起始模式
    patterns = [
        b'^#!/usr/bin/env python',
        b'^# -\\*- coding: utf-8 -\\*-',
        b'^"""',
        b'^\'\'\'',
        b'^from\\s+\\w+',
        b'^import\\s+\\w+',
        b'^class\\s+\\w+',
        b'^def\\s+\\w+',
    ]
    
    # 检查前100字节
    first_100_bytes = content[:100]
    for pattern in patterns:
        if re.search(pattern, first_100_bytes):
            return True
    return False

def fix_file_encoding(file_path):
    """修复文件的编码问题"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 检查文件是否有问题字节
        has_bom = content.startswith(codecs.BOM_UTF8)
        has_null_bytes = b'\x00' in content
        has_invalid_utf8 = False
        
        # 尝试解码为UTF-8，检查是否有无效字符
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            has_invalid_utf8 = True
        
        # 如果没有问题，直接返回
        if not (has_bom or has_null_bytes or has_invalid_utf8):
            return False
        
        # 创建备份
        backup_path = file_path + '.bak'
        with open(backup_path, 'wb') as f:
            f.write(content)
        print(f"已创建备份: {backup_path}")
        
        # 修复内容
        fixed_content = content
        
        # 移除BOM标记
        if has_bom:
            fixed_content = fixed_content[3:]
            print(f"移除了BOM标记: {file_path}")
        
        # 移除空字节
        if has_null_bytes:
            fixed_content = fixed_content.replace(b'\x00', b'')
            print(f"移除了空字节: {file_path}")
        
        # 处理无效的UTF-8字符
        if has_invalid_utf8:
            # 尝试不同的编码方式解码
            for encoding in ['latin1', 'cp1252', 'gbk', 'gb2312', 'big5']:
                try:
                    decoded = fixed_content.decode(encoding, errors='strict')
                    fixed_content = decoded.encode('utf-8')
                    print(f"将编码从 {encoding} 转换为 UTF-8: {file_path}")
                    break
                except UnicodeDecodeError:
                    continue
            
            # 如果上面的编码都不行，使用替换模式
            if has_invalid_utf8:
                try:
                    decoded = fixed_content.decode('utf-8', errors='replace')
                    fixed_content = decoded.encode('utf-8')
                    print(f"替换了无效的UTF-8字符: {file_path}")
                except Exception:
                    pass
        
        # 检查修复后的内容是否还是有效的Python代码
        if not is_valid_python_content(fixed_content):
            print(f"警告: 修复后的内容可能不是有效的Python代码: {file_path}")
            
            # 尝试恢复Python文件的基本结构
            with open(file_path + '.template', 'w', encoding='utf-8') as f:
                f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-

\"\"\"
用户服务模块：提供用户相关的业务逻辑处理
\"\"\"

from typing import Dict, Any, Tuple
from src.modules.auth.models import User
from src.db import db


class UserService:
    \"\"\"用户服务类\"\"\"
    
    # 这里是原文件内容的模板，请根据备份文件手动修复
""")
            print(f"已创建模板文件: {file_path}.template")
        
        # 写入修复后的内容
        with open(file_path, 'wb') as f:
            f.write(fixed_content)
        
        print(f"已修复文件: {file_path}")
        return True
        
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
                if fix_file_encoding(file_path):
                    fixed_files += 1
    
    return fixed_files

if __name__ == "__main__":
    # 直接修复用户服务文件
    file_path = "src/modules/auth/services/user_service.py"
    if os.path.exists(file_path):
        print(f"开始修复文件: {file_path}")
        if fix_file_encoding(file_path):
            print(f"已成功修复文件: {file_path}")
        else:
            print(f"文件无需修复或修复失败: {file_path}")
    else:
        print(f"文件不存在: {file_path}")
    
    # 可选：扫描整个目录
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        print(f"开始扫描目录: {target_dir}")
        fixed_count = scan_directory(target_dir)
        print(f"扫描完成，修复了 {fixed_count} 个文件") 