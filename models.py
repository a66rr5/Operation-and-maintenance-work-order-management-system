# models.py

from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='普通用户')  # '普通用户', 'admin'

    # 添加反向引用，允许从 User 访问其处理的工单
    # lazy='dynamic' 意味着你可以对 ticket_handled 进行进一步的过滤（例如 user.ticket_handled.filter_by(...)）
    tickets_handled = db.relationship('Ticket', backref='handler_obj', lazy='dynamic', foreign_keys='Ticket.handler_id')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='待处理')

    # 将原来的 handler (string) 改为 handler_id (foreign key)
    # 允许 handler_id 为 None，表示工单可以没有处理人
    handler_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # 定义关系，方便通过 ticket.handler 访问 User 对象
    # uselist=False 确保 ticket.handler 返回的是一个 User 对象而不是列表
    # 您之前的模板里用的是 `ticket.handler.username`，所以这里用 `handler` 属性名
    handler = db.relationship('User', foreign_keys=[handler_id], uselist=False)


    location = db.Column(db.String(100), nullable=True)
    reporter = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Ticket {self.id} - {self.ticket_type}>'