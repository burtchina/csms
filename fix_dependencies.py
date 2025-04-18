#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复项目依赖问题
"""

import subprocess
import sys
import os

def main():
    """安装必要的依赖并按正确顺序"""
    print("开始修复项目依赖...")
    
    # 准备安装的包 - 按精确顺序
    packages = [
        "pyasn1==0.4.8",
        "pysmi==0.3.4", 
        "pycryptodomex==3.10.1",
        "pysnmp==4.4.12"
    ]
    
    success = True
    for package in packages:
        print(f"安装 {package}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--force-reinstall", package],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"成功安装 {package}")
        except subprocess.CalledProcessError as e:
            print(f"安装 {package} 失败: {e.stderr}")
            success = False
        except Exception as e:
            print(f"安装 {package} 时出错: {str(e)}")
            success = False
    
    if success:
        print("所有依赖安装成功！")
    else:
        print("部分依赖安装失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    main() 