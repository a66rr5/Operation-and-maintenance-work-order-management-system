from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, admin_required  # 确保 admin_required 装饰器在 app.py 中定义并导入
from extensions import db
from models import User, Ticket
from forms import LoginForm, RegisterForm, TicketForm, UserForm  # 确保所有表单都被导入
from datetime import datetime, timedelta

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from sqlalchemy.orm import joinedload # 导入 joinedload 用于预加载关联数据


# --- 用户认证路由 ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tickets'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('登录成功！', 'success')
            return redirect(next_page or url_for('tickets'))
        else:
            flash('登录失败，请检查用户名和密码。', 'danger')
    return render_template('login.html', form=form, title='登录')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出登录。', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
@admin_required  # 通常只有管理员才能注册新用户
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = form.password.data
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(hashed_password)  # 使用set_password方法来设置密码
        db.session.add(user)
        db.session.commit()
        flash('用户注册成功！', 'success')
        return redirect(url_for('users'))  # 注册成功后跳转到用户列表
    return render_template('register.html', form=form, title='注册用户')


# --- 用户管理路由 ---
@app.route('/users', methods=['GET'])
@admin_required  # 只有管理员才能查看用户列表
def users():
    users = User.query.all()
    return render_template('users.html', users=users, title='用户管理')


@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required  # 只有管理员才能编辑用户
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    # 为 UserForm 传入 original_username 和 user_id
    form = UserForm(obj=user, original_username=user.username, user_id=user.id)

    if form.validate_on_submit():
        # 只有当密码字段有值时才更新密码
        if form.password.data:
            user.set_password(form.password.data)
        user.username = form.username.data
        user.role = form.role.data
        db.session.commit()
        flash('用户已成功更新！', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', form=form, title='编辑用户')


@app.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required  # 只有管理员才能删除用户
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # 防止管理员删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户！', 'danger')
        return redirect(url_for('users'))

    # 删除用户时，将该用户处理的工单的 handler_id 置空
    tickets_assigned_to_user = Ticket.query.filter_by(handler_id=user.id).all()
    for ticket in tickets_assigned_to_user:
        ticket.handler_id = None
    db.session.commit() # 提交对工单的更改

    db.session.delete(user)
    db.session.commit()
    flash(f'用户 {user.username} 已删除！', 'success')
    return redirect(url_for('users'))


# --- 工单管理路由 ---

# 根路径重定向到工单列表
@app.route('/')
def index():
    return redirect(url_for('tickets'))


@app.route('/tickets', methods=['GET'])
@login_required
def tickets():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条工单

    ticket_type_filter = request.args.get('ticket_type')
    status_filter = request.args.get('status')
    handler_filter_username = request.args.get('handler') # 获取的是用户名
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')
    location_filter = request.args.get('location')
    reporter_filter = request.args.get('reporter')

    # 使用 eager loading 预加载 handler 关系，避免 N+1 问题
    query = Ticket.query.options(joinedload(Ticket.handler))

    if ticket_type_filter:
        query = query.filter_by(ticket_type=ticket_type_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    # 针对 handler_id 字段进行过滤，需要通过 User.username 查找 User.id
    if handler_filter_username:
        # 查找匹配的用户 ID
        # 使用 ilike 进行模糊匹配，但精确匹配 ID 效率更高
        handler_users = User.query.filter(User.username.ilike(f'%{handler_filter_username}%')).all()
        handler_ids = [user.id for user in handler_users]
        if handler_ids:
            query = query.filter(Ticket.handler_id.in_(handler_ids))
        else:
            # 如果根据输入的处理人姓名找不到任何用户，则返回空结果
            query = query.filter(Ticket.id == -1) # 保证查询结果为空

    if location_filter:
        query = query.filter(Ticket.location.ilike(f'%{location_filter}%'))
    if reporter_filter:
        query = query.filter(Ticket.reporter.ilike(f'%{reporter_filter}%'))

    if start_date_filter:
        try:
            start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
            query = query.filter(Ticket.created_at >= start_date)
        except ValueError:
            flash('开始日期格式无效，请使用YYYY-MM-DD 格式。', 'danger')
    if end_date_filter:
        try:
            end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
            # 结束日期包含当天，所以加一天
            query = query.filter(Ticket.created_at < end_date + timedelta(days=1))
        except ValueError:
            flash('结束日期格式无效，请使用YYYY-MM-DD 格式。', 'danger')

    tickets_paginated = query.order_by(Ticket.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    ticket_form_instance = TicketForm() # 仍然需要，因为我们要获取 choices
    ticket_types_choices = ticket_form_instance.ticket_type.choices
    ticket_status_choices = ticket_form_instance.status.choices
    # print("DEBUG: ticket_status_choices:", ticket_status_choices) # 调试信息可以移除
    # print("DEBUG: type of ticket_status_choices:", type(ticket_status_choices)) # 调试信息可以移除

    return render_template(
        'tickets.html',
        tickets=tickets_paginated,
        title='工单管理',
        ticket_types_choices=ticket_types_choices,
        ticket_status_choices=ticket_status_choices,
        current_ticket_type_filter=ticket_type_filter,
        current_status_filter=status_filter,
        current_handler_filter=handler_filter_username, # 传递用于回显的用户名
        current_location_filter=location_filter,
        current_reporter_filter=reporter_filter
    )


# --- 工单导出 Excel 功能 ---
@app.route('/tickets/export_excel', methods=['GET'])
@login_required
def export_tickets_excel():
    # 获取与当前“查看工单”页面相同的查询参数
    ticket_type_filter = request.args.get('ticket_type')
    status_filter = request.args.get('status')
    handler_filter = request.args.get('handler')
    start_date_filter = request.args.get('start_date')
    end_date_filter = request.args.get('end_date')
    location_filter = request.args.get('location')
    reporter_filter = request.args.get('reporter')

    # 构建与 tickets 视图函数相同的查询
    query = Ticket.query.options(joinedload(Ticket.handler)) # 确保加载 handler 对象

    if ticket_type_filter:
        query = query.filter_by(ticket_type=ticket_type_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if handler_filter:
        handler_users = User.query.filter(User.username.ilike(f'%{handler_filter}%')).all()
        handler_ids = [user.id for user in handler_users]
        if handler_ids:
            query = query.filter(Ticket.handler_id.in_(handler_ids))
        else:
            query = query.filter(Ticket.id == -1)


    # 应用新字段的过滤
    if location_filter:
        query = query.filter(Ticket.location.ilike(f'%{location_filter}%'))
    if reporter_filter:
        query = query.filter(Ticket.reporter.ilike(f'%{reporter_filter}%'))

    if start_date_filter:
        try:
            start_date = datetime.strptime(start_date_filter, '%Y-%m-%d')
            query = query.filter(Ticket.created_at >= start_date)
        except ValueError:
            pass
    if end_date_filter:
        try:
            end_date = datetime.strptime(end_date_filter, '%Y-%m-%d')
            query = query.filter(Ticket.created_at < end_date + timedelta(days=1))
        except ValueError:
            pass

    tickets_to_export = query.order_by(Ticket.created_at.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "工单数据"

    # 更新表头，加入新字段并移除更新时间
    headers = ["ID", "类型", "说明", "情况", "处理人", "处理地点", "报障人", "创建时间"]
    ws.append(headers)

    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 写入数据，注意顺序
    for ticket in tickets_to_export:
        ws.append([
            ticket.id,
            ticket.ticket_type,
            ticket.description,
            ticket.status,
            ticket.handler.username if ticket.handler else '未分配', # 这里改为访问 username
            ticket.location,
            ticket.reporter,
            ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if cell.value is not None:
                    cell_length = len(str(cell.value))
                    if cell_length > max_length:
                        max_length = cell_length
            except:
                pass
        adjusted_width = (max_length + 2 if max_length > 0 else 10)
        ws.column_dimensions[column].width = adjusted_width

    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    filename = datetime.now().strftime("工单导出_%Y%m%d_%H%M%S.xlsx")
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# --- 新增/编辑工单功能 ---
@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    form = TicketForm()
    # 确保只选择非admin角色的用户作为处理人
    # 将用户 ID 作为值，用户名作为标签
    form.handler.choices = [(str(user.id), user.username) for user in User.query.filter(User.role != 'admin').all()]
    # 如果允许不选处理人，可以添加一个空选项
    form.handler.choices.insert(0, ('', '请选择')) # '请选择' 作为默认空选项

    if form.validate_on_submit():
        # 获取选择的处理人ID (form.handler.data 可能是空字符串)
        selected_handler_id = form.handler.data
        handler_user = None
        if selected_handler_id: # 只有当用户选择了处理人时才去查找对应的 User 对象
            handler_user = User.query.get(selected_handler_id)

        ticket = Ticket(
            ticket_type=form.ticket_type.data,
            description=form.description.data,
            status=form.status.data,
            # 将 User 对象赋值给 ticket.handler 属性，或 None
            handler=handler_user,
            location=form.location.data,
            reporter=form.reporter.data
        )
        db.session.add(ticket)
        db.session.commit()
        flash('工单已成功创建！', 'success')
        return redirect(url_for('tickets'))
    return render_template('ticket_form.html', form=form, title='新增工单', is_edit=False)


@app.route('/ticket/edit/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketForm(obj=ticket) # obj=ticket 会尝试填充字段，但对于handler需要特殊处理

    # 为 form.handler.choices 填充用户 ID 和用户名
    form.handler.choices = [(str(user.id), user.username) for user in User.query.filter(User.role != 'admin').all()]
    form.handler.choices.insert(0, ('', '请选择')) # 允许不选处理人

    # 填充当前工单的处理人
    # 如果 ticket.handler 存在，设置 form.handler.data 为其 ID (字符串形式)
    if not form.is_submitted(): # 仅在 GET 请求时填充
        if ticket.handler:
            form.handler.data = str(ticket.handler.id)
        else:
            form.handler.data = '' # 没有处理人时，默认选中“请选择”

    if form.validate_on_submit():
        selected_handler_id = form.handler.data
        handler_user = None
        if selected_handler_id: # 只有当用户选择了处理人时才去查找对应的 User 对象
            handler_user = User.query.get(selected_handler_id)

        ticket.ticket_type = form.ticket_type.data
        ticket.description = form.description.data
        ticket.status = form.status.data
        ticket.handler = handler_user # 将 User 对象赋值给 ticket.handler
        ticket.location = form.location.data
        ticket.reporter = form.reporter.data
        ticket.updated_at = datetime.now()

        db.session.commit()
        flash('工单已成功更新！', 'success')
        return redirect(url_for('tickets'))

    return render_template('ticket_form.html', form=form, title='编辑工单', is_edit=True)


# --- 单个工单删除功能 ---
@app.route('/ticket/delete/<int:ticket_id>', methods=['POST'])
@admin_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('工单已删除！', 'success')
    return redirect(url_for('tickets'))


# --- 批量删除工单功能 ---
@app.route('/tickets/bulk_delete', methods=['POST'])
@admin_required
def bulk_delete_tickets():
    if not request.is_json:
        return jsonify(status='error', message='请求必须是 JSON 格式'), 400

    data = request.get_json()
    ticket_ids = data.get('ids', [])

    if not ticket_ids:
        return jsonify(status='error', message='没有选择任何工单进行删除。'), 400

    try:
        tickets_to_delete = Ticket.query.filter(Ticket.id.in_(ticket_ids)).all()

        if not tickets_to_delete:
            return jsonify(status='error', message='未找到任何匹配的工单。'), 404

        deleted_count = 0
        for ticket in tickets_to_delete:
            db.session.delete(ticket)
            deleted_count += 1

        db.session.commit()
        return jsonify(status='success', message=f'成功删除了 {deleted_count} 条工单。')

    except Exception as e:
        db.session.rollback()
        return jsonify(status='error', message=f'批量删除失败: {str(e)}'), 500


# --- 工单更新检查功能 ---
@app.route('/tickets/check_for_updates', methods=['GET'])
@login_required
def check_for_tickets_updates():
    # 确保在查询最新工单时，如果涉及 handler 关系，也用 joinedload 避免潜在问题
    latest_ticket = Ticket.query.options(joinedload(Ticket.handler)).order_by(Ticket.updated_at.desc()).first()

    if latest_ticket:
        return jsonify(last_updated=latest_ticket.updated_at.isoformat()), 200

    return jsonify(last_updated=None), 200