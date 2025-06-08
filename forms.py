# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError, Optional
from models import User # 确保导入 User 模型

# 用户登录表单
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

# 用户注册表单 (通常用于管理员创建新用户)
class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password', message='两次输入的密码不一致！')])
    role = SelectField('角色', choices=[('普通用户', '普通用户'), ('admin', '管理员')], validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被注册，请选择其他用户名。')

# 用户编辑表单
class UserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('新密码', validators=[Optional(), Length(min=6)], description='留空表示不修改密码')
    confirm_password = PasswordField('确认新密码', validators=[EqualTo('password', message='两次输入的密码不一致！')], description='留空表示不修改密码')
    role = SelectField('角色', choices=[('普通用户', '普通用户'), ('admin', '管理员')], validators=[DataRequired()])
    submit = SubmitField('更新')

    # validate_username 方法可能需要根据实际需求调整，
    # 比如在编辑时允许用户名不变，但不能改成其他已存在的用户名
    def validate_username(self, username):
        # 仅当用户名改变时，才检查是否重复
        # 如果是编辑现有用户，且用户名未改变，则不触发此验证
        if username.data != self.original_username: # 假设您在路由中设置了 original_username
            user = User.query.filter_by(username=username.data).first()
            if user and user.id != self.user_id: # 确保不是当前用户自己
                raise ValidationError('该用户名已被占用，请选择其他用户名。')

    # 在路由中创建表单实例时，可以通过 obj=user 传入用户对象，
    # 然后在表单实例化后设置 original_username 和 user_id
    def __init__(self, original_username=None, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.user_id = user_id


# 工单表单
class TicketForm(FlaskForm):
    ticket_type = SelectField('工单类型', choices=[
        ('IT', 'IT问题'),
        ('网络', '网络问题'),
        ('设备', '设备故障'),
        ('软件', '软件问题'),
        ('其他', '其他')
    ], validators=[DataRequired()])

    description = TextAreaField('工单说明', validators=[DataRequired(), Length(min=10, max=500)])

    status = SelectField('工单情况', choices=[
        ('部分解决', '部分解决'),
        ('未解决', '未解决'),
        ('已解决', '已解决')
    ], validators=[DataRequired()])

    # 将 handler 字段改为 SelectField，其 choices 将在路由中动态填充
    # Value 是 User.id (字符串形式)，Label 是 User.username
    # Optional() 允许处理人为空，如果工单可以不分配处理人
    handler = SelectField('处理人', validators=[Optional()]) # 或者 DataRequired() 如果处理人必选

    location = StringField('处理地点', validators=[Optional(), Length(max=100)])
    reporter = StringField('报障人', validators=[DataRequired(), Length(max=100)])

    submit = SubmitField('提交')

    # 验证处理人字段是否有效（可选，如果 SelectField 已经通过 choices 限制了有效性）
    # def validate_handler(self, field):
    #     if field.data: # 如果选择了处理人
    #         try:
    #             handler_id = int(field.data)
    #             user = User.query.get(handler_id)
    #             if not user:
    #                 raise ValidationError('选择的处理人无效。')
    #         except ValueError: # 如果 field.data 不是有效的整数 (例如，如果传入了空字符串或非数字)
    #             if field.data != '': # 允许空字符串通过 Optional() 验证
    #                 raise ValidationError('处理人选择无效。')