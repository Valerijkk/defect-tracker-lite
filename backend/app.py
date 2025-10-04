import os, time, logging
from functools import wraps
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone
from collections import Counter

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text
import jwt

# ---- Paths / env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)
DB_PATH = os.path.join(DATA_DIR, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DTL_SQLALCHEMY_DATABASE_URI', 'sqlite:///' + DB_PATH)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB attachments

SECRET_KEY = os.environ.get('SECRET_KEY', 'devsecret')
JWT_EXPIRES_DAYS = int(os.environ.get('JWT_EXPIRES_DAYS', '3'))

# CORS: явно разрешаем Authorization
CORS(app,
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     expose_headers=["Authorization"],
     allow_headers=["Authorization", "Content-Type"])

db = SQLAlchemy(app)

# ---- Logs (rotate 1MB x5)
handler = RotatingFileHandler(os.path.join(LOG_DIR, 'app.log'), maxBytes=1_000_000, backupCount=5, encoding='utf-8')
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# ---- Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), default='engineer')  # manager|engineer

    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')

class Defect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    priority = db.Column(db.String(20), default='medium')  # low|medium|high
    status = db.Column(db.String(20), default='new')       # new|in_progress|review|closed|cancelled
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    attachment_url = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---- DB helpers / init
def ensure_sqlite_column(table: str, column: str, ddl_type: str):
    cur = db.session.execute(text(f'PRAGMA table_info("{table}")'))
    cols = [row[1] for row in cur]
    if column not in cols:
        db.session.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {ddl_type}'))
        db.session.commit()
        app.logger.info('DB migrated: table=%s add column=%s %s', table, column, ddl_type)

with app.app_context():
    db.create_all()
    ensure_sqlite_column('defect', 'attachment_url', 'VARCHAR(255)')

def seed_initial():
    if not User.query.filter_by(email='admin@example.com').first():
        db.session.add(User(email='admin@example.com',
                            password_hash=generate_password_hash('admin123'),
                            role='manager'))
    if not User.query.filter_by(email='eng@example.com').first():
        db.session.add(User(email='eng@example.com',
                            password_hash=generate_password_hash('eng123'),
                            role='engineer'))
    if Project.query.count() == 0:
        p1 = Project(name='Корпус А', description='Объект строительства А')
        p2 = Project(name='Корпус Б', description='Объект строительства Б')
        db.session.add_all([p1, p2])
        db.session.flush()
        db.session.add_all([
            Defect(project_id=p1.id, title='Трещина в стене', description='На 2 этаже', priority='high'),
            Defect(project_id=p1.id, title='Скол плитки', priority='medium'),
            Defect(project_id=p2.id, title='Неплотная дверь', priority='low', status='in_progress'),
        ])
    db.session.commit()

with app.app_context():
    if not app.config.get('TESTING'):
        try:
            seed_initial()
        except Exception as e:
            app.logger.error('Seed error: %s', e)

# ---- Auth helpers
def create_token(user: User) -> str:
    payload = {
        'sub': str(user.id),  # ВАЖНО: sub строго строкой
        'role': user.role,
        'exp': datetime.now(tz=timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token.decode('utf-8') if isinstance(token, bytes) else token

def auth_required(manager_only=False):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            hdr = request.headers.get('Authorization', '')
            if not hdr.startswith('Bearer '):
                return jsonify({'error': 'unauthorized'}), 401
            token = hdr.split(' ', 1)[1].strip()
            if token.startswith("b'") and token.endswith("'"):
                token = token[2:-1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            except Exception as e:
                return jsonify({'error': 'invalid_token', 'detail': str(e)}), 401
            request.user_id = payload.get('sub')  # строка — ок
            request.user_role = payload.get('role')
            if manager_only and request.user_role != 'manager':
                return jsonify({'error': 'forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco

# ---- Routes

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'ts': int(time.time())})

### Auth
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'invalid_credentials'}), 401
    return jsonify({'token': create_token(user), 'role': user.role, 'email': user.email})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    role = (data.get('role') or 'engineer').strip()
    if not email or not password:
        return jsonify({'error': 'email_password_required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'email_exists'}), 409
    if role not in ('engineer',):
        role = 'engineer'
    u = User(email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(u); db.session.commit()
    return jsonify({'token': create_token(u), 'role': u.role, 'email': u.email}), 201

# ---- Setup (dev bootstrap)
@app.route('/api/setup/bootstrap', methods=['POST'])
def setup_bootstrap():
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        return jsonify({'ok': True, 'exists': True}), 200
    if User.query.count() == 0 or not User.query.filter_by(role='manager').first():
        u = User(email='admin@example.com', password_hash=generate_password_hash('admin123'), role='manager')
        db.session.add(u); db.session.commit()
        app.logger.info('Bootstrap admin created')
        return jsonify({'ok': True, 'created': 'admin@example.com'}), 201
    return jsonify({'ok': True, 'skipped': True}), 200

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

# ---- Defects
@app.route('/api/defects', methods=['GET', 'POST'])
@auth_required()
def defects():
    if request.method == 'POST':
        data = request.get_json() or {}
        project_id = data.get('project_id')
        title = (data.get('title') or '').strip()
        if not project_id or not title:
            return jsonify({'error': 'project_id_title_required'}), 400
        d = Defect(
            project_id=project_id,
            title=title,
            description=(data.get('description') or '').strip(),
            priority=(data.get('priority') or 'medium'),
            status=(data.get('status') or 'new'),
            assignee_id=data.get('assignee_id'),
            attachment_url=(data.get('attachment_url') or '').strip()
        )
        db.session.add(d); db.session.commit()
        return jsonify({'id': d.id}), 201

    # GET
    q = Defect.query
    project_id = request.args.get('project_id', type=int)
    if project_id: q = q.filter(Defect.project_id == project_id)
    priority = request.args.get('priority')
    if priority: q = q.filter(Defect.priority == priority)
    status = request.args.get('status')
    if status and status != 'all': q = q.filter(Defect.status == status)
    search = (request.args.get('q') or '').strip().lower()
    if search:
        q = q.filter(db.or_(Defect.title.ilike(f'%{search}%'), Defect.description.ilike(f'%{search}%')))

    items = q.order_by(Defect.id.desc()).all()
    projects_map = {p.id: p.name for p in Project.query.all()}
    def as_dict(d: Defect):
        return {
            'id': d.id, 'project_id': d.project_id, 'project_name': projects_map.get(d.project_id, ''),
            'title': d.title, 'description': d.description, 'priority': d.priority,
            'status': d.status, 'assignee_id': d.assignee_id, 'attachment_url': d.attachment_url,
            'created_at': (d.created_at or datetime.utcnow()).isoformat()
        }
    return jsonify([as_dict(d) for d in items])

@app.route('/api/defects/<int:defect_id>', methods=['PATCH'])
@auth_required()
def update_defect(defect_id):
    d = db.session.get(Defect, defect_id)
    if not d: return jsonify({'error': 'not_found'}), 404
    data = request.get_json() or {}
    for f in ['title','description','priority','status','assignee_id','attachment_url']:
        if f in data: setattr(d, f, data[f])
    db.session.commit()
    return jsonify({'ok': True})

# ---- Uploads
@app.route('/api/upload', methods=['POST'])
@auth_required()
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'file_required'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'filename_required'}), 400
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
    all_def = Defect.query.all()
    per_status = Counter([d.status for d in all_def])
    per_priority = Counter([d.priority for d in all_def])
    per_project = Counter([d.project_id for d in all_def])
    projects = {p.id: p.name for p in Project.query.all()}
    return jsonify({
        'status': per_status,
        'priority': per_priority,
        'project': {projects.get(pid, str(pid)): cnt for pid, cnt in per_project.items()}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT','5000')))
