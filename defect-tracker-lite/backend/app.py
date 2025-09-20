import os
import time
import logging
from functools import wraps
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone, date as date_cls

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text
import jwt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB attachments

SECRET_KEY = os.environ.get('SECRET_KEY', 'devsecret')
JWT_EXPIRES_DAYS = int(os.environ.get('JWT_EXPIRES_DAYS', '3'))

CORS(app)
db = SQLAlchemy(app)

# ---- Logs (rotate 1MB x5)
handler = RotatingFileHandler(os.path.join(LOG_DIR, 'app.log'), maxBytes=1_000_000, backupCount=5, encoding='utf-8')
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# ---- Models ----
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), default='engineer')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')

class Defect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    priority = db.Column(db.String(16), default='medium')  # low|medium|high
    status = db.Column(db.String(16), default='new')       # new|in_progress|review|closed|cancelled
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    attachment_url = db.Column(db.String(255), nullable=True)  # /uploads/...
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project')

# ---- Helpers ----
def create_token(user):
    payload = {
        'sub': str(user.id),  # PyJWT требует строку для sub
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def auth_required(manager_only=False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify({'error': 'missing_token'}), 401
            token = auth.split(' ', 1)[1].strip()
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            except Exception as e:
                return jsonify({'error': 'invalid_token', 'detail': str(e)}), 401
            request.user_id = payload.get('sub')
            request.user_role = payload.get('role')
            if manager_only and request.user_role != 'manager':
                return jsonify({'error': 'forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def _parse_date(s: str):
    return datetime.strptime(s, '%Y-%m-%d').date()

def ensure_sqlite_column(table: str, column: str, ddl_type: str):
    """Мягкая миграция: добавляет колонку, если её ещё нет."""
    cur = db.session.execute(text(f'PRAGMA table_info("{table}")'))
    cols = [row[1] for row in cur]
    if column not in cols:
        db.session.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {ddl_type}'))
        db.session.commit()
        app.logger.info('DB migrated: table=%s, added column=%s %s', table, column, ddl_type)

def init_db():
    db.create_all()
    # auto-migrate new columns
    ensure_sqlite_column('defect', 'attachment_url', 'VARCHAR(255)')

    # Seed users
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(email='admin@example.com', password_hash=generate_password_hash('admin123'), role='manager')
        eng = User(email='eng@example.com', password_hash=generate_password_hash('eng123'), role='engineer')
        db.session.add_all([admin, eng])
        db.session.commit()
    # Seed projects + defects
    if Project.query.count() == 0:
        p1 = Project(name='Корпус А', description='Объект строительства А')
        p2 = Project(name='Корпус Б', description='Объект строительства Б')
        db.session.add_all([p1, p2]); db.session.commit()
        db.session.add_all([
            Defect(project_id=p1.id, title='Трещина на стене', description='2 этаж у лифта', priority='high'),
            Defect(project_id=p1.id, title='Протечка крыши', description='Блок А-3', priority='high'),
            Defect(project_id=p2.id, title='Покраска отсутствует', description='Коридор', priority='low')
        ])
        db.session.commit()

# ---- Routes ----
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'ts': datetime.utcnow().isoformat()}

# ---- Auth
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'invalid_credentials'}), 401
    token = create_token(user)
    return jsonify({'token': token, 'role': user.role, 'email': user.email})

# ---- Projects
@app.route('/api/projects', methods=['GET'])
@auth_required()
def list_projects():
    items = Project.query.order_by(Project.id.desc()).all()
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in items])

@app.route('/api/projects', methods=['POST'])
@auth_required(manager_only=True)
def create_project():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    if not name:
        return jsonify({'error': 'name_required'}), 400
    p = Project(name=name, description=description)
    db.session.add(p); db.session.commit()
    return jsonify({'id': p.id, 'name': p.name, 'description': p.description}), 201

# ---- Defects (filters + create + update)
@app.route('/api/defects', methods=['GET', 'POST'])
@auth_required()
def defects():
    if request.method == 'POST':
        data = request.get_json() or {}
        project_id = data.get('project_id')
        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        priority = (data.get('priority') or 'medium').strip()
        attachment_url = (data.get('attachment_url') or '').strip() or None
        if not project_id or not title:
            return jsonify({'error': 'project_id_and_title_required'}), 400
        if not Project.query.get(project_id):
            return jsonify({'error': 'project_not_found'}), 404
        d = Defect(project_id=project_id, title=title, description=description,
                   priority=priority, attachment_url=attachment_url)
        db.session.add(d); db.session.commit()
        return jsonify({'id': d.id}), 201

    # GET filters: ?project_id=&status=&priority=&q=&date_from=&date_to=
    q = (request.args.get('q') or '').strip().lower()
    project_id = request.args.get('project_id', type=int)
    status = (request.args.get('status') or '').strip()
    priority = (request.args.get('priority') or '').strip()
    date_from = request.args.get('date_from', type=str)
    date_to = request.args.get('date_to', type=str)

    query = Defect.query
    if project_id:
        query = query.filter(Defect.project_id == project_id)
    if status:
        query = query.filter(Defect.status == status)
    if priority:
        query = query.filter(Defect.priority == priority)
    if q:
        like = f'%{q}%'
        query = query.filter((Defect.title.ilike(like)) | (Defect.description.ilike(like)))
    if date_from:
        try:
            dfrom = _parse_date(date_from)
            query = query.filter(Defect.created_at >= datetime(dfrom.year, dfrom.month, dfrom.day))
        except ValueError:
            return jsonify({'error':'bad_date_from', 'need':'YYYY-MM-DD'}), 400
    if date_to:
        try:
            dto = _parse_date(date_to) + timedelta(days=1)
            query = query.filter(Defect.created_at < datetime(dto.year, dto.month, dto.day))
        except ValueError:
            return jsonify({'error':'bad_date_to', 'need':'YYYY-MM-DD'}), 400

    items = query.order_by(Defect.created_at.desc(), Defect.id.desc()).all()
    res = []
    for d in items:
        res.append({
            'id': d.id,
            'project_id': d.project_id,
            'project_name': d.project.name if d.project else None,
            'title': d.title,
            'description': d.description,
            'priority': d.priority,
            'status': d.status,
            'assignee_id': d.assignee_id,
            'attachment_url': d.attachment_url,
            'created_at': d.created_at.isoformat()
        })
    return jsonify(res)

@app.route('/api/defects/<int:defect_id>', methods=['PATCH'])
@auth_required()
def update_defect(defect_id):
    d = Defect.query.get(defect_id)
    if not d:
        return jsonify({'error': 'not_found'}), 404
    data = request.get_json() or {}
    for field in ['title', 'description', 'priority', 'status', 'assignee_id', 'attachment_url']:
        if field in data:
            setattr(d, field, data[field])
    db.session.commit()
    return jsonify({'ok': True})

# ---- Upload attachments
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
@app.route('/api/upload', methods=['POST'])
@auth_required()
def upload():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'file_required'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'error': 'bad_ext', 'allowed': sorted(list(ALLOWED_EXT))}), 400
    fname = f"{int(time.time())}_{secure_filename(file.filename)}"
    path = os.path.join(UPLOAD_DIR, fname)
    file.save(path)
    url = f"/uploads/{fname}"
    app.logger.info('File uploaded: %s', url)
    return jsonify({'url': url}), 201

@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---- Reports
@app.route('/api/reports/summary', methods=['GET'])
@auth_required()
def report_summary():
    """
    Возвращает сводку количества дефектов по статусам и приоритетам,
    опционально по конкретному проекту (?project_id=)
    """
    project_id = request.args.get('project_id', type=int)
    qs = Defect.query
    if project_id:
        qs = qs.filter(Defect.project_id == project_id)

    by_status, by_priority = {}, {}
    for d in qs.all():
        by_status[d.status] = by_status.get(d.status, 0) + 1
        by_priority[d.priority] = by_priority.get(d.priority, 0) + 1

    return jsonify({
        'by_status': [{'status': k, 'count': v} for k, v in sorted(by_status.items())],
        'by_priority': [{'priority': k, 'count': v} for k, v in sorted(by_priority.items())],
        'total': qs.count()
    })

# ---- MAIN
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
