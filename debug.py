#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSMS系统调试启动脚本
这个脚本简化了启动过程并添加了详细日志，用于定位启动问题
"""

import os
import sys
import logging
import traceback

# 配置详细日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 将项目根目录和src目录添加到Python路径
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("==================================================")
print("CSMS系统调试模式启动")
print("==================================================")
print(f"Python路径: {sys.path}")
print(f"当前工作目录: {os.getcwd()}")

try:
    print("步骤1: 导入核心模块...")
    import src.core.db as db_module
    print(f"成功导入db模块: {db_module.__file__}")
    
    print("步骤2: 导入models模块...")
    import src.models as models_module
    print(f"成功导入models模块: {models_module.__file__}")
    print(f"可用的模型: {models_module.__all__}")
    
    print("步骤3: 导入app模块...")
    from src.app import create_app
    print("成功导入create_app函数")
    
    print("步骤4: 创建应用实例...")
    app = create_app('development')
    print("成功创建应用实例")
    
    print("步骤5: 初始化数据库...")
    from src.app import create_tables_and_sample_data
    create_tables_and_sample_data(app)
    print("成功初始化数据库")
    
    print("步骤6: 启动Web服务...")
    app.run(debug=True, host='0.0.0.0')
except Exception as e:
    print(f"启动错误: {e}")
    logger.error(f"详细错误信息:\n{traceback.format_exc()}")
    traceback.print_exc() 