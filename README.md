# 运维工单管理系统

这是一个基于 Flask 框架开发的轻量级运维工单管理系统，旨在帮助团队更高效地管理和追踪运维任务，适用于中小企业对运维工作的追踪，记录，管理等工作。

## 主要功能

* **用户认证与授权：** 用户注册、登录、登出，以及基本的角色（如普通用户、管理员）区分。
* **工单管理：**
    * 创建、编辑、删除工单。
    * 查看工单列表，支持分页显示。
    * 根据工单类型、状态、处理人、地点、报障人、创建日期等条件进行筛选查询。
    * 支持工单数据的批量删除。
* **工单状态流转：** 支持工单从“待处理”到“处理中”、“已解决”、“已关闭”等状态的流转。
* **用户管理：** (如果管理员角色有此功能，可在此说明)
*   * 管理员可以对用户进行查看、创建、删除、修改。
    * 管理员拥有系统最大权限。
* **数据导出：** 支持将工单数据导出为 Excel 文件。
* **实时更新：** (如果您的 AJAX 刷新功能已实现并稳定，可提及) 定期检查工单更新并局部刷新列表。

## 技术栈

* **后端：**
    * Python
    * Flask (Web 框架)
    * Flask-SQLAlchemy (ORM)
    * Flask-Migrate (数据库迁移)
    * Flask-Login (用户认证)
    * Gunicorn (生产环境应用服务器)
    * Werkzeug.security (密码哈希)
    * Openpyxl (Excel 文件处理)
* **前端：**
    * HTML5 / CSS3
    * JavaScript (原生 JS)
    * Bootstrap 5 (UI 框架)
    * Jinja2 (模板引擎)
* **数据库：**
    * SQLite (开发环境/轻量级生产环境)

## 安装与运行

### 1. 克隆项目

```bash
git clone [https://github.com/a66rr5/Operation-and-maintenance-work-order-management-system.git](https://github.com/a66rr5/Operation-and-maintenance-work-order-management-system.git)
cd Operation-and-maintenance-work-order-management-system

2. 创建并激活虚拟环境
Bash

# 对于 Windows
python -m venv .venv
.\.venv\Scripts\activate

# 对于 macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

3. 安装依赖
Bash

pip install -r requirements.txt
如果您没有 requirements.txt 文件，请在激活虚拟环境后执行：

Bash

pip freeze > requirements.txt
然后将生成的文件上传到项目根目录。

4. 数据库初始化与迁移
Bash

# 首次运行，初始化迁移仓库 (如果您的项目是空的，或者之前没初始化过)
flask db init

# 创建迁移脚本 (如果 models.py 有更新)
flask db migrate -m "Initial migration"

# 应用迁移到数据库
flask db upgrade
如果您的数据库文件 site.db 不存在，运行 flask db upgrade 后会自动创建。

5. 设置环境变量
在运行应用之前，请设置必要的环境变量。在开发环境中，您可以直接在终端中设置：

Bash

# 对于 Windows PowerShell
$env:FLASK_APP="app.py"
$env:FLASK_ENV="development"
$env:SECRET_KEY="your_super_secret_key_here" # 请务必替换为一个强随机字符串

# 对于 macOS/Linux Bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY="your_super_secret_key_here" # 请务必替换为一个强随机字符串
在生产环境中，这些变量通常通过 Gunicorn 或 Systemd 服务文件来管理。

6. 运行应用
Bash

flask run
应用将默认在 http://127.0.0.1:5000 运行。

生产环境部署
本系统推荐使用 Nginx 作为反向代理，Gunicorn 作为 WSGI 服务器进行生产部署。具体部署步骤请参考 部署指南。

项目结构
.
├── .venv/                  # Python 虚拟环境
├── migrations/             # Flask-Migrate 数据库迁移脚本
│   ├── versions/           # 迁移版本文件
│   └── ...
├── static/
│   ├── css/
│   │   └── style.css       # 自定义 CSS 样式
│   ├── images/
│   │   └── 1.jpg           # (示例图片，根据实际情况修改)
│   └── js/
│       └── scripts.js      # 自定义 JavaScript
├── templates/
│   ├── base.html           # 基础模板
│   ├── login.html          # 登录页面
│   ├── register.html       # 注册页面
│   ├── ticket_form.html    # 工单创建/编辑表单
│   ├── tickets.html        # 工单列表页面
│   ├── user_form.html      # 用户创建/编辑表单
│   └── users.html          # 用户列表页面
├── .gitignore              # Git 忽略文件配置
├── app.py                  # Flask 应用主文件，应用实例和配置
├── config.py               # 配置类，例如数据库 URI、SECRET_KEY 等
├── extensions.py           # 扩展初始化 (SQLAlchemy, LoginManager 等)
├── forms.py                # WTForms 表单定义
├── models.py               # SQLAlchemy 数据库模型定义
├── requirements.txt        # 项目依赖列表
└── routes.py               # 路由和视图函数定义
贡献
如果您想为本项目贡献代码，请先 Fork 本仓库，然后提交 Pull Request。
