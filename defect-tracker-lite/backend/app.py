import os
import json
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SECRET_KEY = os.environ.get('SECRET_KEY', 'devsecret')
JWT_EXPIRES_DAYS = int(os.environ.get('JWT_EXPIRES_DAYS', '3'))

CORS(app)
db = SQLAlchemy(app)

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
    defects = db.relationship('Defect', backref='project', lazy=True)

class Defect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    priority = db.Column(db.String(16), default='medium')  # low|medium|high
    status = db.Column(db.String(16), default='new')       # new|in_progress|review|closed|cancelled
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---- Helpers ----
def create_token(user):
    payload = {
        'sub': str(user.id),          # было: user.id
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRES_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def auth_required(manager_only=False):
    def decorator(fn):
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
        # keep function metadata
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator

def init_db():
    db.create_all()
    # Seed users
    if not User.query.filter_by(email='admin@example.com').first():
        admin = User(email='admin@example.com', password_hash=generate_password_hash('admin123'), role='manager')
        eng = User(email='eng@example.com', password_hash=generate_password_hash('eng123'), role='engineer')
        db.session.add_all([admin, eng])
        db.session.commit()
    # Seed projects
    if Project.query.count() == 0:
        p1 = Project(name='Корпус А', description='Объект строительства А')
        p2 = Project(name='Корпус Б', description='Объект строительства Б')
        db.session.add_all([p1, p2])
        db.session.commit()
        # Seed defects
        d1 = Defect(project_id=p1.id, title='Трещина на стене', description='На 2 этаже у лифта', priority='high')
        d2 = Defect(project_id=p1.id, title='Протечка крыши', description='Блок А-3', priority='high')
        d3 = Defect(project_id=p2.id, title='Покраска отсутствует', description='Коридор', priority='low')
        db.session.add_all([d1, d2, d3])
        db.session.commit()

# ---- Routes ----
@app.route('/api/health', methods=['GET'])
def health():
    return {'status': 'ok', 'ts': datetime.utcnow().isoformat()}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'invalid_credentials'}), 401
    token = create_token(user)
    return jsonify({'token': token, 'role': user.role, 'email': user.email})

@app.route('/api/projects', methods=['GET'])
@auth_required()
def list_projects():
    items = Project.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'description': p.description} for p in items])

@app.route('/api/projects', methods=['POST'])
@auth_required(manager_only=True)
def create_project():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        return jsonify({'error': 'name_required'}), 400
    p = Project(name=name, description=description)
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name, 'description': p.description}), 201

@app.route('/api/defects', methods=['GET'])
@auth_required()
def list_defects():
    project_id = request.args.get('project_id', type=int)
    q = Defect.query
    if project_id:
        q = q.filter_by(project_id=project_id)
    items = q.order_by(Defect.created_at.desc()).all()
    result = []
    for d in items:
        result.append({
            'id': d.id,
            'project_id': d.project_id,
            'project_name': d.project.name if d.project else None,
            'title': d.title,
            'description': d.description,
            'priority': d.priority,
            'status': d.status,
            'assignee_id': d.assignee_id,
            'created_at': d.created_at.isoformat()
        })
    return jsonify(result)

@app.route('/api/defects', methods=['POST'])
@auth_required()
def create_defect():
    data = request.get_json() or {}
    project_id = data.get('project_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'medium')
    if not project_id or not title:
        return jsonify({'error': 'project_id_and_title_required'}), 400
    if not Project.query.get(project_id):
        return jsonify({'error': 'project_not_found'}), 404
    d = Defect(project_id=project_id, title=title, description=description, priority=priority)
    db.session.add(d)
    db.session.commit()
    return jsonify({'id': d.id}), 201

@app.route('/api/defects/<int:defect_id>', methods=['PATCH'])
@auth_required()
def update_defect(defect_id):
    d = Defect.query.get(defect_id)
    if not d:
        return jsonify({'error': 'not_found'}), 404
    data = request.get_json() or {}
    for field in ['title', 'description', 'priority', 'status', 'assignee_id']:
        if field in data:
            setattr(d, field, data[field])
    db.session.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)