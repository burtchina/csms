#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
校园安全管理系统(CSMS) - 主运行脚本
"""

import os
import sys
import warnings
import argparse
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# 抑制警告
os.environ['PYTHONWARNINGS'] = 'ignore:.*TripleDES.*:DeprecationWarning'
os.environ['PYTHONWARNINGS'] = 'ignore:.*Blowfish.*:DeprecationWarning'
os.environ['CRYPTOGRAPHY_SUPPRESS_DEPRECATION_WARNINGS'] = '1'
warnings.filterwarnings('ignore', category=DeprecationWarning)

def main():
    """主函数，解析参数并启动应用"""
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='校园安全管理系统启动脚本')
    parser.add_argument('--reset-db', action='store_true', help='重置数据库（删除所有数据并重建）')
    parser.add_argument('--port', type=int, default=5000, help='指定端口号，默认5000')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址，默认0.0.0.0')
    parser.add_argument('--env', type=str, default='development', help='指定运行环境，默认development')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("校园安全管理系统 (CSMS) 启动")
    logger.info("=" * 50)
    logger.info(f"运行环境: {args.env}")
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = args.env
    
    try:
        # 导入应用
        logger.info("正在创建应用实例...")
        from src.app import create_app, create_tables_and_sample_data
        
        # 创建应用
        app = create_app(args.env)
        
        # 初始化数据库
        logger.info("正在初始化数据库...")
        if args.reset_db:
            logger.warning("已启用数据库重置选项，将删除所有现有数据!")
            # 如果需要实现数据库重置功能，可以在这里添加代码
        
        create_tables_and_sample_data(app)
        logger.info("数据库初始化完成")
        
        # 启动应用
        logger.info(f"启动Web服务，地址: http://{args.host}:{args.port}/")
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    except ImportError as e:
        logger.error(f"导入错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 