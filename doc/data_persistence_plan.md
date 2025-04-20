# 校园安全管理系统(CSMS)数据持久化实现方案

## 当前持久化现状

基于项目最新进度，系统已采用以下技术进行数据持久化：

- **ORM框架**：SQLAlchemy 1.4.23, Flask-SQLAlchemy 2.5.1
- **数据迁移**：Flask-Migrate 3.1.0
- **数据库支持**：SQLite (开发环境), MySQL 8.0 (生产环境)
- **数据缓存**：Redis 3.5.3
- **数据库文件**：存储于`data/`目录

## 持久化方案改进建议

### 1. 数据库配置优化

```python
# config.py 数据库配置示例
class Config:
    # 基础配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,  # 连接回收时间(秒)
        'pool_timeout': 20,   # 连接超时时间(秒)
        'pool_size': 10,      # 连接池大小
        'max_overflow': 5     # 最大溢出连接数
    }
    
    # 日志配置
    SQLALCHEMY_ECHO = False  # 生产环境关闭SQL日志
    SQLALCHEMY_RECORD_QUERIES = False  # 生产环境关闭查询记录
    
class DevelopmentConfig(Config):
    # SQLite开发环境配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/dev.sqlite'
    SQLALCHEMY_ECHO = True  # 开发环境开启SQL日志
    
class ProductionConfig(Config):
    # MySQL生产环境配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/csms?charset=utf8mb4'
    # 为生产环境禁用池回收超时
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_timeout': 20,
        'pool_size': 20,      # 生产环境更大的连接池
        'max_overflow': 10    # 生产环境更大的最大溢出连接数
    }
```

### 2. 高级模型设计

系统已完善的核心模型结构：

- **设备类型模型**
  ```python
  class DeviceType(db.Model):
      __tablename__ = 'device_types'
      
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(50), nullable=False, unique=True)
      description = db.Column(db.String(200))
      created_at = db.Column(db.DateTime, default=datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      
      # 关联关系
      devices = db.relationship('Device', backref='type', lazy='dynamic')
      
      def __repr__(self):
          return f'<DeviceType {self.name}>'
  ```

- **设备管理模型**
  ```python
  class Device(db.Model):
      __tablename__ = 'devices'
      
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String(100), nullable=False)
      category = db.Column(db.String(50), nullable=False)
      type_id = db.Column(db.Integer, db.ForeignKey('device_types.id'))
      model = db.Column(db.String(100))
      location = db.Column(db.String(100))
      ip_address = db.Column(db.String(15), unique=True)
      mac_address = db.Column(db.String(17), unique=True)
      status = db.Column(db.String(20), default='offline', 
                         info={'choices': ['online', 'offline', 'maintenance', 'error']})
      firmware_version = db.Column(db.String(50))
      installation_date = db.Column(db.Date)
      last_maintenance = db.Column(db.DateTime)
      next_maintenance = db.Column(db.DateTime)
      manufacturer = db.Column(db.String(100))
      serial_number = db.Column(db.String(100), unique=True)
      description = db.Column(db.Text)
      warranty_expiry = db.Column(db.Date)
      specs = db.Column(db.JSON)
      created_at = db.Column(db.DateTime, default=datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      
      # 通信凭证（加密存储）
      ssh_username = db.Column(db.String(100))
      ssh_password = db.Column(db.String(255))  # 存储加密后的密码
      snmp_community = db.Column(db.String(100))
      snmp_version = db.Column(db.String(10), default='v2c')
      
      # 关联关系
      fault_records = db.relationship('FaultRecord', backref='device', lazy='dynamic')
      maintenance_records = db.relationship('MaintenanceRecord', backref='device', lazy='dynamic')
      performance_records = db.relationship('PerformanceRecord', backref='device', lazy='dynamic')
      thresholds = db.relationship('PerformanceThreshold', backref='device', lazy='dynamic')
      
      __table_args__ = (
          db.Index('idx_device_status', 'status'),  # 状态索引
          db.Index('idx_device_type_location', 'type_id', 'location'),  # 复合索引
      )
      
      @property
      def is_online(self):
          return self.status == 'online'
          
      def update_status(self, new_status):
          """更新设备状态并记录状态变更"""
          if self.status != new_status:
              self.status = new_status
              # 记录状态变更事件
              event = DeviceStatusEvent(
                  device_id=self.id,
                  old_status=self.status,
                  new_status=new_status
              )
              db.session.add(event)
      
      def to_dict(self):
          """转换为字典表示"""
          return {
              'id': self.id,
              'name': self.name,
              'category': self.category,
              'type': self.type.name if self.type else None,
              'type_id': self.type_id,
              'model': self.model,
              'status': self.status,
              'location': self.location,
              'ip_address': self.ip_address,
              'mac_address': self.mac_address,
              'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
              'next_maintenance': self.next_maintenance.isoformat() if self.next_maintenance else None,
          }
  ```

- **故障记录模型**
  ```python
  class FaultRecord(db.Model):
      __tablename__ = 'fault_records'
      
      id = db.Column(db.Integer, primary_key=True)
      title = db.Column(db.String(100), nullable=False)
      device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
      fault_type = db.Column(db.String(50), nullable=False)
      severity = db.Column(db.String(20), nullable=False, 
                           info={'choices': ['low', 'medium', 'high', 'critical']})
      description = db.Column(db.Text)
      status = db.Column(db.String(20), default='pending',
                         info={'choices': ['pending', 'processing', 'resolved']})
      reported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
      assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
      resolution = db.Column(db.Text)
      created_at = db.Column(db.DateTime, default=datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      resolved_at = db.Column(db.DateTime)
      
      # 关联关系
      attachments = db.relationship('FaultAttachment', backref='fault', lazy='dynamic')
      
      __table_args__ = (
          db.Index('idx_fault_device', 'device_id'),
          db.Index('idx_fault_status', 'status'),
      )
  ```

- **维护记录模型**
  ```python
  class MaintenanceRecord(db.Model):
      __tablename__ = 'maintenance_records'
      
      id = db.Column(db.Integer, primary_key=True)
      title = db.Column(db.String(100), nullable=False)
      device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
      maintenance_type = db.Column(db.String(50), nullable=False,
                                   info={'choices': ['routine', 'repair', 'upgrade']})
      description = db.Column(db.Text)
      status = db.Column(db.String(20), default='planned',
                         info={'choices': ['planned', 'inprogress', 'completed', 'cancelled']})
      start_time = db.Column(db.DateTime, nullable=False)
      end_time = db.Column(db.DateTime, nullable=False)
      assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
      completed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
      completion_notes = db.Column(db.Text)
      created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
      created_at = db.Column(db.DateTime, default=datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      completed_at = db.Column(db.DateTime)
      
      # 关联关系
      items = db.relationship('MaintenanceItem', backref='maintenance', lazy='dynamic')
      
      __table_args__ = (
          db.Index('idx_maintenance_device', 'device_id'),
          db.Index('idx_maintenance_status', 'status'),
          db.Index('idx_maintenance_time', 'start_time', 'end_time'),
      )
  ```

- **性能数据模型**
  ```python
  class PerformanceRecord(db.Model):
      __tablename__ = 'performance_records'
      
      id = db.Column(db.Integer, primary_key=True)
      device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
      metric_id = db.Column(db.String(50), nullable=False)  # cpu_usage, memory_usage, etc.
      value = db.Column(db.Float, nullable=False)
      unit = db.Column(db.String(20))  # %, MB, °C, etc.
      recorded_at = db.Column(db.DateTime, default=datetime.now, index=True)
      
      __table_args__ = (
          db.Index('idx_perf_device_metric', 'device_id', 'metric_id'),
          db.Index('idx_perf_device_time', 'device_id', 'recorded_at'),
          # 带分区的索引（MySQL支持）
          # db.Index('idx_perf_time_device_metric', 'recorded_at', 'device_id', 'metric_id'),
      )
      
      # 实现数据分区（按时间分片）
      @classmethod
      def create_partition_table(cls, year, month):
          """创建按月分区的性能数据表"""
          partition_name = f'performance_records_{year}_{month:02d}'
          return type(
              partition_name,
              (cls,),
              {
                  '__tablename__': partition_name,
                  '__table_args__': (
                      {'mysql_partition': f'PARTITION p_{year}_{month:02d}'}
                  )
              }
          )
  ```

- **性能阈值模型**
  ```python
  class PerformanceThreshold(db.Model):
      __tablename__ = 'performance_thresholds'
      
      id = db.Column(db.Integer, primary_key=True)
      device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
      metric_id = db.Column(db.String(50), nullable=False)
      warning_threshold = db.Column(db.Float)
      critical_threshold = db.Column(db.Float)
      enabled = db.Column(db.Boolean, default=True)
      created_at = db.Column(db.DateTime, default=datetime.now)
      updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      
      __table_args__ = (
          db.UniqueConstraint('device_id', 'metric_id', name='uq_threshold_device_metric'),
      )
  ```

### 3. 性能优化策略

为提升系统数据访问性能，建议实施以下优化策略：

#### 3.1 查询优化

```python
# 优化查询示例

# 不好的查询方式（多次查询）
def get_device_with_faults(device_id):
    device = Device.query.get(device_id)
    faults = FaultRecord.query.filter_by(device_id=device_id).all()
    return device, faults

# 优化后的查询（使用join）
def get_device_with_faults_optimized(device_id):
    result = db.session.query(Device, FaultRecord)\
        .outerjoin(FaultRecord, Device.id == FaultRecord.device_id)\
        .filter(Device.id == device_id).all()
    device = result[0][0] if result else None
    faults = [r[1] for r in result if r[1] is not None]
    return device, faults

# 使用缓存进一步优化
@cache.cached(timeout=60, key_prefix='device_detail_%s')
def get_device_details_cached(device_id):
    return get_device_with_faults_optimized(device_id)
```

#### 3.2 数据分页与懒加载

```python
# 分页查询示例
@app.route('/devices')
def device_list():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # 限制最大条数
    
    # 延迟加载关联数据，避免N+1查询问题
    query = Device.query.options(
        joinedload(Device.type),  # 预加载类型数据
        lazyload(Device.fault_records),  # 懒加载故障记录
        lazyload(Device.maintenance_records)  # 懒加载维护记录
    )
    
    # 根据条件筛选
    if request.args.get('status'):
        query = query.filter(Device.status == request.args.get('status'))
    if request.args.get('type_id'):
        query = query.filter(Device.type_id == request.args.get('type_id'))
    
    # 执行分页查询
    pagination = query.paginate(page=page, per_page=per_page)
    return render_template('device/list.html', pagination=pagination)
```

#### 3.3 缓存策略实现

```python
# 配置多级缓存
cache_config = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
    'CACHE_DEFAULT_TIMEOUT': 300,  # 默认缓存5分钟
    'CACHE_KEY_PREFIX': 'csms_'
}
cache = Cache(app, config=cache_config)

# 常用数据缓存示例
@cache.cached(timeout=3600, key_prefix='device_types')  # 缓存1小时
def get_all_device_types():
    return DeviceType.query.all()

# 针对个别频繁访问的数据使用更长的缓存时间
@cache.cached(timeout=86400, key_prefix='system_settings')  # 缓存1天
def get_system_settings():
    return SystemSettings.query.first()

# 动态缓存键生成
def make_cache_key_for_device(*args, **kwargs):
    device_id = request.view_args.get('device_id')
    return f'device_detail_{device_id}'

@app.route('/device/<int:device_id>')
@cache.cached(timeout=60, key_prefix=make_cache_key_for_device)
def device_detail(device_id):
    device = Device.query.get_or_404(device_id)
    return render_template('device/detail.html', device=device)

# 缓存失效策略
def invalidate_device_cache(device_id):
    cache.delete(f'device_detail_{device_id}')
    cache.delete('device_list')  # 也可能需要失效列表缓存
```

#### 3.4 数据归档与分区

对于大量的历史数据（如性能数据、日志等），建议实施数据归档和分区策略：

```python
# 数据归档策略实现
def archive_old_performance_data():
    """将90天前的性能数据归档到历史表"""
    threshold_date = datetime.now() - timedelta(days=90)
    
    # 创建新的分区表存储历史数据
    year_month = threshold_date.strftime('%Y_%m')
    archive_table = f'performance_records_archive_{year_month}'
    
    with db.engine.connect() as conn:
        # 创建归档表（如果不存在）
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {archive_table} LIKE performance_records
        """)
        
        # 移动数据到归档表
        conn.execute(f"""
            INSERT INTO {archive_table}
            SELECT * FROM performance_records 
            WHERE recorded_at < :threshold_date
        """, {'threshold_date': threshold_date})
        
        # 从主表删除已归档数据
        conn.execute("""
            DELETE FROM performance_records 
            WHERE recorded_at < :threshold_date
        """, {'threshold_date': threshold_date})
        
    # 记录归档操作
    app.logger.info(f'已归档 {threshold_date} 之前的性能数据到 {archive_table}')
```

#### 3.5 批量操作优化

```python
# 批量插入优化
def bulk_insert_performance_data(records):
    """批量插入性能数据"""
    if not records:
        return
        
    # 使用批量插入替代多次单条插入
    db.session.bulk_insert_mappings(
        PerformanceRecord, 
        [
            {
                'device_id': r['device_id'],
                'metric_id': r['metric_id'],
                'value': r['value'],
                'unit': r.get('unit'),
                'recorded_at': r.get('recorded_at', datetime.now())
            }
            for r in records
        ]
    )
    db.session.commit()
```

### 4. 数据安全策略

#### 4.1 敏感数据加密

```python
# 设备访问凭证加密存储
from cryptography.fernet import Fernet

# 生成加密密钥并安全存储
def generate_encryption_key():
    return Fernet.generate_key()

# 在设备模型中实现加密方法
class Device(db.Model):
    # ... 其他属性 ...
    
    def set_ssh_password(self, password):
        # 从配置或安全存储获取密钥
        key = app.config['ENCRYPTION_KEY']
        f = Fernet(key)
        # 加密密码
        self.ssh_password = f.encrypt(password.encode()).decode()
    
    def get_ssh_password(self):
        if not self.ssh_password:
            return None
        # 从配置或安全存储获取密钥
        key = app.config['ENCRYPTION_KEY']
        f = Fernet(key)
        # 解密密码
        return f.decrypt(self.ssh_password.encode()).decode()
```

#### 4.2 数据访问控制

```python
# 实现数据访问控制层
class DeviceAccessControl:
    @staticmethod
    def can_user_view_device(user, device):
        """检查用户是否有权限查看设备"""
        # 管理员可以查看所有设备
        if user.is_admin:
            return True
        # 设备负责人可以查看自己负责的设备
        if device.assigned_to == user.id:
            return True
        # 根据用户角色和区域权限检查
        if user.has_permission('device:view'):
            return DeviceAccessControl.is_device_in_user_area(user, device)
        return False
    
    @staticmethod
    def is_device_in_user_area(user, device):
        """检查设备是否在用户负责的区域内"""
        user_areas = UserArea.query.filter_by(user_id=user.id).all()
        allowed_areas = [area.area_id for area in user_areas]
        return device.location_area_id in allowed_areas
    
    @staticmethod
    def filter_devices_by_user_permission(query, user):
        """根据用户权限过滤设备查询结果"""
        if user.is_admin:
            return query  # 管理员无过滤
        
        if user.has_permission('device:view:all'):
            return query  # 有全部查看权限无过滤
            
        # 过滤只返回用户有权限查看的设备
        user_areas = UserArea.query.filter_by(user_id=user.id).all()
        allowed_areas = [area.area_id for area in user_areas]
        
        return query.filter(
            db.or_(
                Device.assigned_to == user.id,
                Device.location_area_id.in_(allowed_areas)
            )
        )
```

### 5. 总结与建议

基于系统当前状态和未来发展需求，提出以下数据持久化优化建议：

1. **数据库迁移**：开发环境继续使用SQLite，生产环境建议迁移至MySQL 8.0，提供更好的性能和扩展性
2. **连接池管理**：合理配置连接池参数，优化数据库连接资源利用
3. **索引优化**：为常用查询字段建立合适的索引，提高查询效率
4. **分区策略**：对海量历史数据实施表分区(特别是性能数据)，提高查询性能
5. **批量操作**：使用批量操作替代多次单条操作，减少数据库负载
6. **缓存策略**：针对不同数据类型设计多层次缓存策略，减轻数据库压力
7. **查询优化**：优化SQL查询，避免N+1查询问题，使用JOIN操作减少查询次数
8. **数据归档**：实施数据归档策略，定期将历史数据转移到归档表或历史数据库
9. **安全措施**：加密存储敏感信息，实现细粒度的数据访问控制
10. **监控系统**：实施数据库性能监控，及时发现和解决性能瓶颈 