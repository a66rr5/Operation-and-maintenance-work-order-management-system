# app.py

from flask import Flask, flash, redirect, url_for # 导入 flash, redirect, url_for 以便在 admin_required 中使用
from flask_login import LoginManager, current_user # 导入 current_user
import os
from datetime import datetime # <--- 这个导入很重要，用于工单的创建时间和更新时间
from flask_migrate import Migrate # <--- 之前安装的，用于数据库迁移
from functools import wraps # 导入 functools 用于创建装饰器

# 先导入 extensions
from extensions import db, login_manager # db 和 login_manager 在 extensions.py 中定义

# 创建 Flask 应用实例
app = Flask(__name__)
# 配置 Jinja2 环境，加载 'do' 扩展
app.jinja_env.add_extension('jinja2.ext.do')
# 配置
app.config['SECRET_KEY'] = 'your_very_secret_key_that_you_should_change' # 更改为更安全的密钥
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # SQLite 数据库路径
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展，确保在 app 实例创建后调用 init_app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login' # 未登录时重定向的视图函数
login_manager.login_message_category = 'info' # 登录提示消息的分类git

# 如果使用 Flask-Migrate，这里需要初始化它
migrate = Migrate(app, db) # <--- 初始化 Flask-Migrate

# 定义用户加载函数（在 models.py 导入之后）
# 注意：LoginManager 的 user_loader 装饰器需要在 models.py 中的 User 模型被定义后才能使用
from models import User # 在这里导入 User 模型

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 在这里添加 admin_required 装饰器的定义 ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('您没有权限访问此页面。', 'danger')
            return redirect(url_for('login')) # 或者重定向到主页，例如 return redirect(url_for('tickets'))
        return f(*args, **kwargs)
    return decorated_function
# --- 装饰器定义结束 ---


# --- 数据库初始化和默认管理员创建（移到这里，并确保在应用上下文中）---
# 这一整块代码需要放在所有路由定义之前，但要在 app 实例和 db 实例初始化之后
with app.app_context():
    db.create_all() # 创建所有数据库表

    # 检查是否已存在管理员用户，如果没有则创建
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', role='admin')
        admin_user.set_password('admin123') # 请在生产环境中更改此默认密码
        db.session.add(admin_user)
        db.session.commit()
        print("已创建默认管理员用户：admin/admin123")


# 现在才导入路由，确保所有配置、扩展初始化、装饰器定义以及数据库初始化都已完成
# 放在文件末尾，这样在 routes.py 被导入时，所有依赖都已准备就绪
from routes import *


if __name__ == '__main__':
    app.run(debug=True)