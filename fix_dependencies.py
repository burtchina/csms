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
    
    # Flask相关依赖 - 关键版本控制
    flask_packages = [
        "itsdangerous==2.0.1",
        "werkzeug==2.0.3",
        "Flask==2.0.1"
    ]
    
    # 其他依赖
    packages = [
        "pyasn1==0.4.8",
        "pysmi==0.3.4", 
        "pycryptodomex==3.10.1",
        "pysnmp==4.4.12"
    ]
    
    # 首先安装Flask及其关键依赖
    print("====== 安装Flask及其关键依赖 ======")
    success = install_packages(flask_packages)
    
    # 然后安装其他依赖
    print("\n====== 安装其他依赖 ======")
    success = install_packages(packages) and success
    
    if success:
        print("\n所有依赖安装成功！")
    else:
        print("\n部分依赖安装失败，请检查错误信息")
    
    # 检查Flask及其依赖版本
    check_flask_version()
    
    return success

def install_packages(packages):
    """安装包列表"""
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
    return success

def check_flask_version():
    """检查Flask及其依赖的版本"""
    check_packages = ["Flask", "werkzeug", "itsdangerous"]
    print("\n====== 检查安装的版本 ======")
    for package in check_packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                if line.startswith("Name:") or line.startswith("Version:"):
                    print(line.strip())
            print("")
        except Exception as e:
            print(f"检查 {package} 版本失败: {str(e)}")

if __name__ == "__main__":
    main() 