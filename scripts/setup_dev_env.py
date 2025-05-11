#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
开发环境设置脚本
用于快速设置开发环境并验证配置
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 确保脚本可以在任何目录下运行
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

def setup_dependencies():
    """安装正确版本的依赖"""
    print("===== 安装项目依赖 =====")
    try:
        subprocess.run([sys.executable, "fix_dependencies.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("安装依赖失败，请查看错误消息")
        return False

def fix_import_issues():
    """修复项目中的导入问题"""
    print("\n===== 修复导入问题 =====")
    # 在这里我们修复policy_repository.py的导入问题
    policy_repo_path = Path("src/modules/policy/repositories/policy_repository.py")
    
    if not policy_repo_path.exists():
        print(f"警告: 找不到文件 {policy_repo_path}")
        return False
        
    print(f"正在修复 {policy_repo_path}...")
    
    try:
        with open(policy_repo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经修复
        if "from src.modules.policy.models.policy_template import PolicyTemplate" in content:
            print("导入已经是正确的，无需修复")
            return True
        
        # 替换导入语句
        old_import = "from src.modules.policy.models.policy import Policy, PolicyTemplate, PolicyDeployment, PolicyAuditLog, PolicyAlert"
        new_imports = """from src.modules.policy.models.policy import Policy
from src.modules.policy.models.policy_template import PolicyTemplate
from src.modules.policy.models.policy_deployment import PolicyDeployment
from src.modules.policy.models.policy_audit_log import PolicyAuditLog
from src.modules.policy.models.policy_alert import PolicyAlert"""
        
        if old_import in content:
            content = content.replace(old_import, new_imports)
            
            with open(policy_repo_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print("成功修复导入问题")
            return True
        else:
            print("文件内容已被修改，无法自动修复导入")
            return False
            
    except Exception as e:
        print(f"修复导入问题时出错: {e}")
        return False

def run_tests():
    """运行隔离测试"""
    print("\n===== 运行隔离测试 =====")
    isolated_test = Path("tests/policy/test_isolated_service.py")
    
    if not isolated_test.exists():
        print(f"警告: 找不到测试文件 {isolated_test}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(isolated_test), "-v"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ 隔离测试成功通过!")
            return True
        else:
            print("❌ 测试失败")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def check_flask_imports():
    """检查Flask导入是否正常"""
    print("\n===== 检查Flask导入 =====")
    test_code = """
import sys
try:
    import flask
    from flask import Flask, _app_ctx_stack
    print("Flask导入测试: 成功")
    print(f"Flask版本: {flask.__version__}")
    sys.exit(0)
except ImportError as e:
    print(f"Flask导入测试: 失败 - {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"检查Flask导入时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='设置开发环境')
    parser.add_argument('--skip-deps', action='store_true', help='跳过依赖安装')
    parser.add_argument('--skip-imports', action='store_true', help='跳过导入修复')
    parser.add_argument('--skip-tests', action='store_true', help='跳过测试运行')
    args = parser.parse_args()
    
    print(f"项目根目录: {PROJECT_ROOT}")
    
    success = True
    
    if not args.skip_deps:
        deps_success = setup_dependencies()
        success = success and deps_success
    
    if not args.skip_imports:
        imports_success = fix_import_issues()
        success = success and imports_success
    
    # 总是检查Flask导入
    flask_success = check_flask_imports()
    success = success and flask_success
    
    if not args.skip_tests:
        tests_success = run_tests()
        success = success and tests_success
    
    if success:
        print("\n✅ 所有步骤成功完成！开发环境已设置好。")
    else:
        print("\n❌ 某些步骤失败，请检查上述错误消息。")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 