#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移工具函数
用于将旧模型数据迁移到新模型结构
"""

import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from src.core.db import db
# 导入新旧模型
from src.models import Device, DeviceType, PerformanceRecord, Threshold
from src.modules.performance.models import PerformanceData

# 设置日志
logger = logging.getLogger(__name__)

def migrate_performance_data():
    """
    将旧的PerformanceData数据迁移到新的PerformanceRecord模型
    
    Returns:
        dict: 迁移结果统计
    """
    try:
        # 获取所有旧数据记录
        logger.debug("查询所有旧性能数据记录...")
        old_records = PerformanceData.query.all()
        
        # 统计信息
        stats = {
            'total': len(old_records),
            'migrated': 0,
            'errors': 0
        }
        
        if not old_records:
            logger.info("没有找到旧性能数据记录，跳过迁移")
            return stats
        
        logger.info(f"开始迁移 {stats['total']} 条性能数据记录")
        
        # 批量处理，每批500条
        batch_size = 500
        for i in range(0, len(old_records), batch_size):
            batch = old_records[i:i+batch_size]
            
            # 为每批数据创建新记录
            new_records = []
            for old_record in batch:
                try:
                    # 创建新记录
                    new_record = PerformanceRecord(
                        device_id=old_record.device_id,
                        cpu_usage=old_record.cpu_usage,
                        memory_usage=old_record.memory_usage,
                        bandwidth_usage=None,  # 旧数据没有带宽使用率
                        recorded_at=old_record.timestamp,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    new_records.append(new_record)
                    stats['migrated'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"处理记录 {old_record.id} 时出错: {str(e)}")
            
            # 批量保存到数据库
            try:
                db.session.bulk_save_objects(new_records)
                db.session.commit()
                logger.info(f"成功迁移批次 {i//batch_size + 1}, 处理 {len(batch)} 条记录")
            except SQLAlchemyError as e:
                stats['errors'] += len(batch)
                stats['migrated'] -= len(batch)
                db.session.rollback()
                logger.error(f"保存批次 {i//batch_size + 1} 时出错: {str(e)}")
        
        logger.info(f"迁移完成: 总计 {stats['total']} 条记录, 成功 {stats['migrated']} 条, 失败 {stats['errors']} 条")
        return stats
        
    except Exception as e:
        logger.error(f"迁移过程中出错: {str(e)}")
        return {
            'total': 0,
            'migrated': 0,
            'errors': 0,
            'error_message': str(e)
        }

def verify_database_structure():
    """
    验证数据库结构是否与模型定义一致
    
    Returns:
        dict: 验证结果
    """
    try:
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # 验证必要的表是否存在
        required_tables = ['devices', 'device_types', 'performance_records', 'thresholds']
        missing_tables = [table for table in required_tables if table not in tables]
        
        # 检查表结构
        issues = []
        
        # 检查devices表结构
        if 'devices' in tables:
            columns = {col['name']: col for col in inspector.get_columns('devices')}
            # 确保必要的列存在
            required_columns = ['id', 'name', 'ip_address']
            for col in required_columns:
                if col not in columns:
                    issues.append(f"设备表缺少必要的列: {col}")
        
        # 检查performance_records表结构
        if 'performance_records' in tables:
            columns = {col['name']: col for col in inspector.get_columns('performance_records')}
            # 确保必要的列存在
            required_columns = ['id', 'device_id', 'cpu_usage', 'memory_usage', 'recorded_at']
            for col in required_columns:
                if col not in columns:
                    issues.append(f"性能记录表缺少必要的列: {col}")
        
        return {
            'status': 'ok' if not missing_tables and not issues else 'issues',
            'missing_tables': missing_tables,
            'issues': issues,
            'tables': tables
        }
        
    except Exception as e:
        logger.error(f"验证数据库结构时出错: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def add_missing_columns():
    """
    为表添加缺少的列
    
    Returns:
        dict: 添加结果
    """
    try:
        from sqlalchemy import inspect, text
        
        added_columns = []
        
        # 检查devices表结构
        inspector = inspect(db.engine)
        if 'devices' in inspector.get_table_names():
            # 获取当前列
            existing_columns = {col['name'] for col in inspector.get_columns('devices')}
            logger.debug(f"当前devices表列: {existing_columns}")
            
            # 需要添加的列及其类型
            columns_to_add = {
                'firmware_version': 'VARCHAR(50)',
                'serial_number': 'VARCHAR(50)',
                'device_code': 'VARCHAR(50)',
                'mac_address': 'VARCHAR(20)',
                'manufacturer': 'VARCHAR(100)',
                'model': 'VARCHAR(100)',
                'purchase_date': 'DATE',
                'warranty_period': 'INTEGER',
                'notes': 'TEXT',
                'username': 'VARCHAR(50)',
                'password': 'VARCHAR(100)',
                'port': 'INTEGER',
                'connection_protocol': 'VARCHAR(20)'
            }
            
            # 添加缺少的列
            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    sql_text = text(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type}")
                    try:
                        # 使用正确的SQLAlchemy执行方式
                        with db.engine.connect() as conn:
                            conn.execute(sql_text)
                            conn.commit()
                        added_columns.append(f"devices.{col_name}")
                        logger.info(f"成功添加列 {col_name} 到 devices 表")
                    except Exception as e:
                        logger.error(f"添加列 {col_name} 时出错: {str(e)}")
        else:
            logger.warning("devices表不存在，无法添加列")
        
        # 检查performance_records表结构
        if 'performance_records' in inspector.get_table_names():
            # 获取当前列
            existing_columns = {col['name'] for col in inspector.get_columns('performance_records')}
            logger.debug(f"当前performance_records表列: {existing_columns}")
            
            # 需要添加的列及其类型
            columns_to_add = {
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            }
            
            # 添加缺少的列
            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    sql_text = text(f"ALTER TABLE performance_records ADD COLUMN {col_name} {col_type}")
                    try:
                        # 使用正确的SQLAlchemy执行方式
                        with db.engine.connect() as conn:
                            conn.execute(sql_text)
                            conn.commit()
                        added_columns.append(f"performance_records.{col_name}")
                        logger.info(f"成功添加列 {col_name} 到 performance_records 表")
                    except Exception as e:
                        logger.error(f"添加列 {col_name} 时出错: {str(e)}")
        else:
            logger.warning("performance_records表不存在，无法添加列")
        
        return {
            'status': 'ok',
            'added_columns': added_columns
        }
        
    except Exception as e:
        logger.error(f"添加缺少列时出错: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

def run_compatibility_fixes():
    """
    运行兼容性修复，确保系统正常运行
    
    这个函数应该在应用启动时调用，以确保数据库和模型之间的兼容性
    """
    try:
        logger.info("开始运行兼容性修复")
        
        # 1. 验证数据库结构
        db_structure = verify_database_structure()
        if db_structure['status'] != 'ok':
            logger.warning(f"数据库结构存在问题: {db_structure}")
            
            # 如果缺少表，尝试创建
            if db_structure['missing_tables']:
                logger.info(f"尝试创建缺失的表: {db_structure['missing_tables']}")
                if 'devices' in db_structure['missing_tables']:
                    db.create_all(tables=[Device.__table__])
                if 'device_types' in db_structure['missing_tables']:
                    db.create_all(tables=[DeviceType.__table__])
                if 'performance_records' in db_structure['missing_tables']:
                    db.create_all(tables=[PerformanceRecord.__table__])
                if 'thresholds' in db_structure['missing_tables']:
                    db.create_all(tables=[Threshold.__table__])
        
        # 添加缺少的列
        columns_result = add_missing_columns()
        logger.info(f"添加缺少列结果: {columns_result}")
        
        # 2. 检查如果旧数据存在但新表为空，则迁移数据
        old_count = 0
        new_count = 0
        try:
            old_count = PerformanceData.query.count()
        except Exception as e:
            logger.error(f"检查旧性能数据时出错: {str(e)}")
            # 继续执行，不要中断程序
        
        try:
            new_count = PerformanceRecord.query.count()
        except Exception as e:
            logger.error(f"检查新性能数据时出错: {str(e)}")
            # 创建性能记录表，确保表存在
            try:
                db.create_all(tables=[PerformanceRecord.__table__])
                logger.info("已创建性能记录表")
                new_count = 0  # 新创建的表，记录为0
            except Exception as create_err:
                logger.error(f"创建性能记录表时出错: {str(create_err)}")
        
        # 安全地尝试数据迁移
        if old_count > 0 and new_count == 0:
            try:
                logger.info(f"检测到 {old_count} 条旧性能数据记录，但新表为空，开始数据迁移")
                migration_result = migrate_performance_data()
                logger.info(f"数据迁移结果: {migration_result}")
            except Exception as migrate_err:
                logger.error(f"迁移性能数据时出错: {str(migrate_err)}")
        else:
            logger.info(f"无需迁移数据。旧记录: {old_count}, 新记录: {new_count}")
        
        logger.info("兼容性修复完成")
        return {
            'status': 'ok',
            'old_records': old_count,
            'new_records': new_count,
            'columns_result': columns_result
        }
        
    except Exception as e:
        logger.error(f"运行兼容性修复时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'status': 'error',
            'message': str(e)
        } 