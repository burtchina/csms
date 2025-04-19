#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导入修复脚本
扫描所有Python文件并将相对导入修改为绝对导入
"""

import os
import re
import sys
import logging
from typing import List, Dict, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义应修复的导入模式和对应的替换模式
IMPORT_PATTERNS = [
    # 模块化导入修复 (from x import y -> from src.x import y)
    (r'from\s+core\.', 'from src.core.'),
    (r'from\s+models\b', 'from src.models'),
    (r'from\s+modules\.', 'from src.modules.'),
    (r'from\s+migration_utils\b', 'from src.migration_utils'),
    (r'from\s+config\b', 'from src.config'),
    
    # 直接导入修复 (import x -> import src.x)
    (r'import\s+core\.', 'import src.core.'),
    (r'import\s+models\b', 'import src.models'),
    (r'import\s+modules\.', 'import src.modules.'),
    (r'import\s+migration_utils\b', 'import src.migration_utils'),
    (r'import\s+config\b', 'import src.config'),
]

# 不应该修改的文件和目录
EXCLUDE_PATHS = [
    '__pycache__',
    '.git',
    'venv',
    'env',
    '.env',
    '.venv',
    'migrations'
]

def should_skip_file(file_path: str) -> bool:
    """检查是否应该跳过该文件"""
    for exclude in EXCLUDE_PATHS:
        if exclude in file_path:
            return True
    return False

def fix_imports(file_path: str) -> Tuple[bool, int]:
    """
    修复单个文件中的导入
    
    Args:
        file_path: 要修复的文件路径
        
    Returns:
        Tuple[bool, int]: (是否成功修复, 修复的导入数量)
    """
    if should_skip_file(file_path):
        logger.debug(f"跳过文件: {file_path}")
        return False, 0
    
    logger.info(f"正在处理文件: {file_path}")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_count = 0
        
        # 应用所有导入修复模式
        for pattern, replacement in IMPORT_PATTERNS:
            # 计算修复前的匹配数量
            matches_before = len(re.findall(pattern, content))
            # 应用修复
            content = re.sub(pattern, replacement, content)
            # 计算修复后的匹配数量
            matches_after = len(re.findall(replacement, content))
            # 更新修复计数
            fixed_count += matches_before - matches_after
        
        # 如果有修改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已修复 {fixed_count} 处导入问题: {file_path}")
            return True, fixed_count
        else:
            logger.debug(f"文件未修改: {file_path}")
            return False, 0
            
    except UnicodeDecodeError:
        logger.warning(f"无法解码文件(可能是二进制文件): {file_path}")
        return False, 0
    except Exception as e:
        logger.error(f"处理文件时出错: {file_path}, 错误: {str(e)}")
        return False, 0

def scan_directory(directory: str) -> Dict[str, int]:
    """
    扫描目录，修复所有Python文件
    
    Args:
        directory: 要扫描的目录路径
        
    Returns:
        Dict[str, int]: 统计信息
    """
    stats = {
        'processed_files': 0,  # 处理的文件数
        'fixed_files': 0,      # 修改的文件数
        'fixed_imports': 0,    # 修复的导入数
        'errors': 0            # 错误数量
    }
    
    try:
        # 扫描目录中的所有文件
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    stats['processed_files'] += 1
                    
                    try:
                        success, fixed_count = fix_imports(file_path)
                        if success:
                            stats['fixed_files'] += 1
                            stats['fixed_imports'] += fixed_count
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"处理文件失败: {file_path}, 错误: {str(e)}")
    except Exception as e:
        logger.error(f"扫描目录时出错: {directory}, 错误: {str(e)}")
    
    return stats

def main():
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='修复Python文件中的导入问题')
    parser.add_argument('--dir', type=str, default='src', help='要扫描的目录路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 检查目录是否存在
    if not os.path.isdir(args.dir):
        logger.error(f"错误: 找不到目录 {args.dir}")
        sys.exit(1)
    
    logger.info(f"开始扫描目录: {args.dir}")
    stats = scan_directory(args.dir)
    
    # 打印统计信息
    logger.info("=" * 50)
    logger.info("导入修复完成!")
    logger.info(f"处理文件数: {stats['processed_files']}")
    logger.info(f"修改文件数: {stats['fixed_files']}")
    logger.info(f"修复导入数: {stats['fixed_imports']}")
    logger.info(f"错误数量: {stats['errors']}")
    logger.info("=" * 50)
    
    if stats['fixed_imports'] > 0:
        logger.info("现在可以尝试运行应用了: python run.py")
    else:
        logger.info("未发现需要修复的导入问题。")

if __name__ == '__main__':
    main() 