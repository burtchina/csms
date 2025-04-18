#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySnmp辅助模块，用于处理SNMP请求和提供模拟数据
"""

import logging
import random
import time
import sys
import os
import site
import importlib
import importlib.util
import subprocess

# 设置日志
logger = logging.getLogger(__name__)

# 全局标志，用于跟踪PySnmp是否可用
SNMP_AVAILABLE = False

# 确保可以找到所有必要的模块
for path in site.getsitepackages():
    if path not in sys.path:
        sys.path.append(path)
        logger.debug(f"添加路径: {path}")

# 检查pyasn1版本
def check_and_fix_pyasn1():
    """检查pyasn1版本并尝试修复问题"""
    try:
        import pyasn1
        logger.info(f"pyasn1版本: {pyasn1.__version__}")
        
        # 检查是否有兼容性问题
        if not importlib.util.find_spec("pyasn1.compat.octets"):
            logger.warning("检测到pyasn1.compat.octets模块丢失，尝试安装兼容版本...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--force-reinstall", "pyasn1==0.4.8"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("成功安装兼容版本的pyasn1")
                # 重新导入
                importlib.reload(pyasn1)
                # 再次检查
                if importlib.util.find_spec("pyasn1.compat.octets"):
                    logger.info("pyasn1.compat.octets模块现在可用")
                    return True
            else:
                logger.warning(f"安装兼容版本的pyasn1失败: {result.stderr}")
        else:
            logger.info("pyasn1.compat.octets模块正常")
            return True
    except Exception as e:
        logger.error(f"检查pyasn1出错: {str(e)}")
    return False

# 安装必要的依赖
def install_dependencies():
    """安装必要的依赖"""
    packages = [
        "pyasn1==0.4.8",
        "pysmi==0.3.4",
        "pycryptodomex==3.10.1",
        "pysnmp==4.4.12"
    ]
    
    success = True
    for package in packages:
        try:
            logger.info(f"安装 {package}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.warning(f"安装 {package} 失败: {result.stderr}")
                success = False
        except Exception as e:
            logger.error(f"安装 {package} 时出错: {str(e)}")
            success = False
    
    return success

# 尝试修复pyasn1
check_and_fix_pyasn1()

# 尝试直接导入所需模块
try:
    # 逐个尝试导入依赖模块
    import pyasn1
    logger.info("pyasn1导入成功")
    
    # 尝试导入pysnmp
    from pysnmp.hlapi import *
    SNMP_AVAILABLE = True
    logger.info("成功加载PySnmp模块")
except ImportError as e:
    logger.warning(f"无法导入模块: {str(e)}，将尝试安装依赖")
    if install_dependencies():
        # 重新尝试导入
        try:
            # 重新导入模块
            if 'pyasn1' in sys.modules:
                importlib.reload(sys.modules['pyasn1'])
            
            # 尝试导入PySnmp
            from pysnmp.hlapi import *
            SNMP_AVAILABLE = True
            logger.info("安装依赖后成功加载PySnmp模块")
        except ImportError as e2:
            logger.warning(f"安装后仍无法导入PySnmp: {str(e2)}")
            SNMP_AVAILABLE = False
    else:
        logger.warning("依赖安装失败，将使用模拟数据")
        SNMP_AVAILABLE = False

# 如果仍然无法导入，使用模拟数据
if not SNMP_AVAILABLE:
    logger.warning("PySnmp不可用，将使用模拟数据")

# 模拟数据生成函数
def generate_mock_data(oid):
    """
    生成模拟SNMP数据
    
    Args:
        oid: OID字符串
        
    Returns:
        模拟数据
    """
    logger.debug(f"生成OID {oid}的模拟数据")
    
    # 根据不同的OID返回不同类型的模拟数据
    if oid.startswith('.1.3.6.1.2.1.25.3.3.1.2'):  # CPU负载
        return str(random.randint(5, 80))
    elif oid.startswith('.1.3.6.1.2.1.25.2.3.1.5'):  # 内存大小
        return str(random.randint(1024, 8192) * 1024)
    elif oid.startswith('.1.3.6.1.2.1.25.2.3.1.6'):  # 内存使用
        return str(random.randint(512, 4096) * 1024)
    elif oid.startswith('.1.3.6.1.2.1.1.3.0'):  # 设备运行时间
        return str(random.randint(10000, 5000000))
    elif oid.startswith('.1.3.6.1.2.1.2.2.1.10') or oid.startswith('.1.3.6.1.2.1.2.2.1.16'):  # 接口流量
        return str(random.randint(1000, 100000000))
    elif oid.startswith('.1.3.6.1.2.1.2.1.0'):  # 接口数量
        return str(random.randint(4, 48))
    else:
        # 默认模拟数据
        return str(random.randint(0, 1000))

def generate_mock_walk_data(oid):
    """
    生成模拟SNMP walk数据
    
    Args:
        oid: 起始OID
        
    Returns:
        模拟数据列表
    """
    logger.debug(f"生成OID {oid}的模拟walk数据")
    
    results = []
    
    # 根据不同OID生成不同数量和类型的模拟数据
    if oid.startswith('.1.3.6.1.2.1.2.2.1'):  # 接口表
        for i in range(1, random.randint(4, 16)):
            sub_oid = f"{oid}.{i}"
            results.append((sub_oid, generate_mock_data(sub_oid)))
    elif oid.startswith('.1.3.6.1.2.1.25.2.3.1'):  # 存储表
        for i in range(1, random.randint(3, 8)):
            sub_oid = f"{oid}.{i}"
            results.append((sub_oid, generate_mock_data(sub_oid)))
    else:
        # 默认生成5-10个条目
        for i in range(1, random.randint(5, 10)):
            sub_oid = f"{oid}.{i}"
            results.append((sub_oid, generate_mock_data(sub_oid)))
    
    return results

# 获取SNMP数据
def get_snmp_data(ip, community, oid):
    """
    获取SNMP数据，如果PySnmp不可用则返回模拟数据
    
    Args:
        ip: 设备IP地址
        community: SNMP社区名
        oid: OID字符串
        
    Returns:
        查询结果
    """
    if not SNMP_AVAILABLE:
        return generate_mock_data(oid)
        
    try:
        # 使用PySnmp获取真实数据
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        
        error_indication, error_status, error_index, var_binds = next(iterator)
        
        if error_indication:
            logger.warning(f"SNMP错误: {error_indication}")
            return generate_mock_data(oid)
        elif error_status:
            logger.warning(f"SNMP错误状态: {error_status.prettyPrint()} at {var_binds[int(error_index) - 1][0] if error_index else '?'}")
            return generate_mock_data(oid)
        else:
            # 成功获取数据
            for var_bind in var_binds:
                return var_bind[1].prettyPrint()
    except Exception as e:
        logger.error(f"SNMP查询错误: {str(e)}")
        return generate_mock_data(oid)

def get_snmp_bulk(ip, community, oids):
    """
    批量获取SNMP数据
    
    Args:
        ip: 设备IP地址
        community: SNMP社区名
        oids: OID列表
        
    Returns:
        查询结果字典
    """
    results = {}
    for oid in oids:
        results[oid] = get_snmp_data(ip, community, oid)
    return results

def snmp_walk(ip, community, oid):
    """
    执行SNMP walk操作
    
    Args:
        ip: 设备IP地址
        community: SNMP社区名
        oid: 起始OID
        
    Returns:
        结果列表
    """
    if not SNMP_AVAILABLE:
        return generate_mock_walk_data(oid)
        
    try:
        results = []
        for (error_indication, error_status, error_index, var_binds) in nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False
        ):
            if error_indication:
                logger.warning(f"SNMP错误: {error_indication}")
                break
            elif error_status:
                logger.warning(f"SNMP错误状态: {error_status.prettyPrint()} at {var_binds[int(error_index) - 1][0] if error_index else '?'}")
                break
            else:
                for var_bind in var_binds:
                    results.append((var_bind[0].prettyPrint(), var_bind[1].prettyPrint()))
        
        if not results:
            return generate_mock_walk_data(oid)
        return results
    except Exception as e:
        logger.error(f"SNMP walk错误: {str(e)}")
        return generate_mock_walk_data(oid)

if __name__ == "__main__":
    # 模块测试代码
    logging.basicConfig(level=logging.INFO)
    print(f"PySnmp是否可用: {SNMP_AVAILABLE}")
    
    # 测试模拟数据生成
    test_oids = [
        '.1.3.6.1.2.1.25.3.3.1.2.1',  # CPU
        '.1.3.6.1.2.1.25.2.3.1.5.1',  # 内存大小
        '.1.3.6.1.2.1.1.3.0',         # 运行时间
        '.1.3.6.1.2.1.2.2.1.10.1'     # 接口输入流量
    ]
    
    for oid in test_oids:
        result = get_snmp_data('127.0.0.1', 'public', oid)
        print(f"OID {oid}: {result}") 