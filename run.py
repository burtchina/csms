#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 主运行脚本
"""

import os
import sys
import warnings
import subprocess
import argparse

# 添加项目根目录到Python路径
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

# 忽略和抑制警告 - 设置环境变量（必须在导入其他模块前设置）
os.environ['PYTHONWARNINGS'] = 'ignore:.*TripleDES.*:DeprecationWarning:cryptography'
os.environ['PYTHONWARNINGS'] = 'ignore:.*Blowfish.*:DeprecationWarning:cryptography'
os.environ['CRYPTOGRAPHY_SUPPRESS_DEPRECATION_WARNINGS'] = '1'

# 忽略特定警告
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*TripleDES.*')
warnings.filterwarnings('ignore', message='.*Blowfish.*')

def set_env_vars():
    """设置必要的环境变量"""
    # 确保PyASN1模块能被找到
    python_path = os.environ.get('PYTHONPATH', '')
    site_packages = subprocess.check_output(
        [sys.executable, "-c", "import site; print(';'.join(site.getsitepackages()))"],
        text=True
    ).strip()
    
    if site_packages and site_packages not in python_path:
        if python_path:
            os.environ['PYTHONPATH'] = f"{python_path};{site_packages}"
        else:
            os.environ['PYTHONPATH'] = site_packages
    
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")
    return True

def check_dependencies():
    """检查并安装依赖"""
    try:
        # 检查install_dependencies.py是否存在
        deps_script = os.path.join(base_dir, 'src', 'install_dependencies.py')
        if os.path.exists(deps_script):
            print("正在检查项目依赖...")
            result = subprocess.run([sys.executable, deps_script], 
                                   capture_output=True, 
                                   text=True)
            if result.returncode != 0:
                print("依赖安装失败，请手动安装依赖")
                print(f"错误信息: {result.stderr}")
                return False
            print("依赖检查完成")
            return True
        else:
            print("未找到依赖安装脚本，跳过依赖检查")
            return True
    except Exception as e:
        print(f"依赖检查失败: {str(e)}")
        return False

def run_app(host='0.0.0.0', port=5000, reset_db=False):
    """运行应用程序"""
    try:
        # 构建参数
        cmd = [sys.executable, os.path.join(base_dir, 'src', 'app.py'), 
               '--host', host, '--port', str(port)]
        
        if reset_db:
            cmd.append('--reset-db')
            
        # 运行应用
        print(f"正在启动应用，访问地址: http://{host}:{port}")
        subprocess.run(cmd, env=os.environ)  # 传递当前环境变量
        return True
    except Exception as e:
        print(f"应用启动失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='校园安全管理系统启动脚本')
    parser.add_argument('--reset-db', action='store_true', help='重置数据库（删除所有数据并重建）')
    parser.add_argument('--port', type=int, default=5000, help='指定端口号，默认5000')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址，默认0.0.0.0')
    parser.add_argument('--skip-deps', action='store_true', help='跳过依赖检查')
    args = parser.parse_args()
    
    print("=" * 50)
    print("校园安全管理系统 (CSMS) 启动")
    print("=" * 50)
    
    # 设置环境变量
    set_env_vars()
    
    # 检查依赖
    if not args.skip_deps:
        if not check_dependencies():
            print("依赖检查失败，程序退出")
            sys.exit(1)
    
    # 运行应用
    run_app(host=args.host, port=args.port, reset_db=args.reset_db) 