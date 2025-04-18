#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安装CSMS项目依赖
"""

import subprocess
import sys
import os

def install_package(package):
    """安装指定的包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"成功安装 {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"安装 {package} 失败")
        return False

def main():
    """主函数"""
    print("开始安装CSMS项目依赖...")
    
    # 安装PySnmp相关的依赖（特定版本顺序）
    pysnmp_deps = [
        "pyasn1==0.4.8",      # 安装特定版本的pyasn1，兼容PySnmp 4.4.12
        "pysmi==0.3.4",       # 安装特定版本的pysmi
        "pycryptodomex==3.10.1",
        "pysnmp==4.4.12"      # 最后安装PySnmp
    ]
    
    # 先安装PySnmp相关依赖
    print("正在安装PySnmp相关依赖...")
    for package in pysnmp_deps:
        install_package(package)
    
    # 安装其他基本依赖
    packages = [
        "Flask==2.0.1",
        "SQLAlchemy==1.4.23",
        "Flask-SQLAlchemy==2.5.1",
        "Flask-Login==0.5.0",
        "Flask-WTF==0.15.1",
        "Flask-Migrate==3.1.0",
        "paramiko==2.7.2",
        "netmiko==3.4.0"
    ]
    
    # 尝试从requirements.txt安装依赖
    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'requirements.txt')
    if os.path.exists(req_path):
        print("发现requirements.txt文件，从文件安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("成功从requirements.txt安装依赖")
        except subprocess.CalledProcessError:
            print("从requirements.txt安装依赖失败，将尝试单独安装各依赖")
            for package in packages:
                install_package(package)
    else:
        print("未找到requirements.txt文件，将单独安装各依赖")
        for package in packages:
            install_package(package)
    
    print("CSMS项目依赖安装完成")

if __name__ == "__main__":
    main() 