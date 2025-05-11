#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行脚本
使用方法：python tests/run_tests.py
支持参数：
    --unit-only：仅运行单元测试
    --integration-only：仅运行集成测试
    默认运行所有测试
"""

import os
import sys
import unittest
import argparse

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

# 导入测试模块
from tests.modules.policy.test_policy_database import TestPolicyDatabase
from tests.modules.policy.test_policy_integration import TestPolicyIntegration
# 导入策略服务测试类
from tests.policy.test_policy_service import TestPolicyService

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='运行测试套件')
    parser.add_argument('--unit-only', action='store_true', help='仅运行单元测试')
    parser.add_argument('--integration-only', action='store_true', help='仅运行集成测试')
    parser.add_argument('--service-only', action='store_true', help='仅运行服务层测试')
    args = parser.parse_args()
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # 根据参数添加测试用例
    if args.service_only:
        print("仅运行服务层测试...")
        # 注意: pytest测试不能使用unittest的TestLoader加载
        print("请使用 pytest 命令运行 tests/policy/test_policy_service.py")
        print("例如: python -m pytest tests/policy/test_policy_service.py -v")
        sys.exit(0)
    elif args.integration_only:
        print("仅运行集成测试...")
        test_suite.addTest(loader.loadTestsFromTestCase(TestPolicyIntegration))
    elif args.unit_only:
        print("仅运行单元测试...")
        test_suite.addTest(loader.loadTestsFromTestCase(TestPolicyDatabase))
    else:
        print("运行所有测试...")
        # 添加单元测试
        test_suite.addTest(loader.loadTestsFromTestCase(TestPolicyDatabase))
        # 添加集成测试
        test_suite.addTest(loader.loadTestsFromTestCase(TestPolicyIntegration))
        # 注意：服务层测试需要使用pytest运行
        print("注意: 服务层测试需要单独使用pytest运行")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 根据测试结果设置退出代码
    sys.exit(not result.wasSuccessful()) 