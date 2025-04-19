#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSMS 监控模块依赖安装脚本
"""

import sys
import subprocess
import os
import platform

def print_status(message):
    """打印状态消息"""
    print(f"\n[*] {message}")

def install_package(package, version=None):
    """安装指定的包"""
    pkg_name = f"{package}=={version}" if version else package
    print_status(f"正在安装 {pkg_name}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
        print(f"✓ {pkg_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"× {pkg_name} 安装失败: {e}")
        return False

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """主函数"""
    print_status("CSMS 监控模块依赖安装")
    print("=" * 50)
    
    # 检测操作系统
    system = platform.system()
    print_status(f"操作系统: {system} {platform.version()}")
    
    # 检测 Python 版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_status(f"Python 版本: {python_version}")
    
    if sys.version_info < (3, 7):
        print("× 错误: Python 版本必须 >= 3.7")
        sys.exit(1)
    
    # 定义需要安装的包
    packages = [
        ("paramiko", "2.11.0"),  # SSH 参数化连接
        ("netmiko", "4.1.2"),    # 网络设备连接库
        ("pyasn1", "0.4.8"),     # ASN.1 支持
        ("pysnmp", "4.4.12"),    # SNMP 支持
        ("flask-sqlalchemy", "3.0.3"),  # Flask 数据库 ORM
        ("pycryptodomex", "3.17"),  # 加密库 (pysnmp 依赖)
    ]
    
    # 安装所有包
    print_status("开始安装依赖包")
    
    success_count = 0
    for package, version in packages:
        pkg_name = package.split('[')[0]  # 处理 package[extra] 格式
        if check_package(pkg_name):
            print(f"✓ {package} 已安装")
            success_count += 1
        else:
            if install_package(package, version):
                success_count += 1
    
    # 总结
    print("\n" + "=" * 50)
    if success_count == len(packages):
        print(f"✓ 所有 {len(packages)} 个依赖包安装成功!")
        print("\n现在您可以使用 CSMS 的实时监控功能了。")
    else:
        print(f"× 注意: {len(packages) - success_count} 个包安装失败。")
        print("  某些监控功能可能无法正常工作。")
    
    print("\n如果遇到问题，请查阅 docs/实时监控使用指南.md")

if __name__ == "__main__":
    main() 