"""
测试配置文件
"""
import os
import sys
import pytest

# 获取项目根目录的绝对路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 将项目根目录添加到Python模块搜索路径中
sys.path.insert(0, project_root)

@pytest.fixture(scope="session")
def app_root():
    """返回应用根目录"""
    return project_root 