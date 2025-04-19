# 数据迁移与兼容性管理笔记

CSMS系统实现了一套完整的数据迁移和兼容性管理机制，主要通过`src/migration_utils.py`实现。这些工具函数确保系统在模型结构变更时能平稳过渡。

## 核心功能

### 1. 数据迁移工具

`migrate_performance_data()`函数负责将旧的性能数据模型迁移到新模型：

```python
def migrate_performance_data():
    # 获取所有旧数据记录
    old_records = PerformanceData.query.all()
    
    # 批量处理，每批500条
    batch_size = 500
    for i in range(0, len(old_records), batch_size):
        batch = old_records[i:i+batch_size]
        
        # 为每批数据创建新记录
        new_records = []
        for old_record in batch:
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
```

这种批量处理方式有效避免了大量数据一次性加载到内存中，提高了迁移效率。

### 2. 数据库结构验证

`verify_database_structure()`函数检查数据库结构是否与当前模型定义一致：

```python
def verify_database_structure():
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
```

这种验证确保了系统可以及早发现并处理数据库结构问题。

### 3. 兼容性修复

`run_compatibility_fixes()`函数在应用启动时自动运行，确保数据库和模型的兼容性：

```python
def run_compatibility_fixes():
    # 1. 验证数据库结构
    db_structure = verify_database_structure()
    if db_structure['status'] != 'ok':
        # 如果缺少表，尝试创建
        if db_structure['missing_tables']:
            if 'devices' in db_structure['missing_tables']:
                db.create_all(tables=[Device.__table__])
            # ...其他表的创建
    
    # 2. 检查如果旧数据存在但新表为空，则迁移数据
    old_count = PerformanceData.query.count()
    new_count = PerformanceRecord.query.count()
    
    if old_count > 0 and new_count == 0:
        migration_result = migrate_performance_data()
```

## 应用程序集成

这些迁移工具在应用启动时通过`app.py`中的代码自动运行：

```python
# 在应用上下文中运行数据库兼容性修复
with app.app_context():
    try:
        compatibility_result = run_compatibility_fixes()
        logger.info(f"数据库兼容性检查结果: {compatibility_result}")
    except Exception as e:
        logger.error(f"运行数据库兼容性修复时出错: {str(e)}")
```

## 最佳实践

从这些实现中，我们可以总结以下数据迁移最佳实践：

1. **批量处理**：分批处理大量数据
2. **错误处理**：每个步骤都有完善的错误处理机制
3. **结构验证**：主动验证数据库结构是否符合期望
4. **自动修复**：检测到问题后尝试自动修复
5. **详细日志**：记录详细的操作日志，便于问题排查
6. **回滚机制**：操作失败时能够回滚更改

这些技术确保了系统在数据模型演化过程中的稳定性和向后兼容性。 