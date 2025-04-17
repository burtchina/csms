from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 创建数据库实例
db = SQLAlchemy()

# 创建登录管理器实例
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录后再访问此页面'
login_manager.login_message_category = 'warning' 