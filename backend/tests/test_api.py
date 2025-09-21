import os, io, tempfile, json, pytest
from werkzeug.security import generate_password_hash
from app import app, db, User, Project, Defect

@pytest.fixture()
def client():
    """Изолированная SQLite-БД, идемпотентные сиды, логин -> token в client.token"""
    fd, db_path = tempfile.mkstemp()
    try:
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///' + db_path)
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            # seed users + 1 проект
            db.session.add_all([
                User(email='admin@example.com', password_hash=generate_password_hash('admin123'), role='manager'),
                User(email='eng@example.com',   password_hash=generate_password_hash('eng123'),   role='engineer'),
                Project(name='P1', description='')
            ])
            db.session.commit()

        with app.test_client() as c:
            r = c.post('/api/auth/login', json={'email': 'admin@example.com', 'password': 'admin123'})
            assert r.status_code == 200, r.data
            c.token = json.loads(r.data)['token']
            yield c
    finally:
        os.close(fd)
        os.unlink(db_path)

def H(c): return {'Authorization': f'Bearer {c.token}'}
def j(r):  return r.status_code, (json.loads(r.data) if r.data else None)

def test_health(client):
    code, data = j(client.get('/api/health'))
    assert code == 200 and data['status'] == 'ok'

def test_login_ok_and_bad(client):
    code, data = j(client.post('/api/auth/login', json={'email':'admin@example.com','password':'admin123'}))
    assert code == 200 and 'token' in data
    code2, _ = j(client.post('/api/auth/login', json={'email':'admin@example.com','password':'nope'}))
    assert code2 == 401

def test_projects_role_access(client):
    # engineer не может POST /projects
    code, data = j(client.post('/api/auth/login', json={'email':'eng@example.com','password':'eng123'}))
    r = client.post('/api/projects', json={'name':'X'}, headers={'Authorization':'Bearer '+data['token']})
    assert r.status_code == 403
    # manager может
    r2 = client.post('/api/projects', json={'name':'X'}, headers=H(client))
    assert r2.status_code == 201

def test_defect_create_and_filters(client):
    # создаём несколько дефектов
    client.post('/api/defects', json={'project_id':1, 'title':'Leak', 'priority':'high'}, headers=H(client))
    client.post('/api/defects', json={'project_id':1, 'title':'Crack', 'priority':'low'},  headers=H(client))
    # фильтр по q и priority
    code, data = j(client.get('/api/defects?q=Leak&priority=high', headers=H(client)))
    assert code == 200 and len(data) == 1 and data[0]['title'] == 'Leak'

def test_upload_and_patch_attachment(client):
    file_data = (io.BytesIO(b'PDFDATA'), 'a.pdf')
    r = client.post('/api/upload', data={'file': file_data}, headers=H(client), content_type='multipart/form-data')
    assert r.status_code == 201, r.data
    url = json.loads(r.data)['url']
    # привяжем к дефекту
    r2 = client.post('/api/defects', json={'project_id':1,'title':'WithAttach','priority':'medium','attachment_url':url}, headers=H(client))
    assert r2.status_code == 201
    did = json.loads(r2.data)['id']
    r3 = client.patch(f'/api/defects/{did}', json={'status':'closed'}, headers=H(client))
    assert j(r3)[0] == 200

def test_report_summary(client):
    client.post('/api/defects', json={'project_id':1, 'title':'A', 'priority':'high',   'status':'new'},    headers=H(client))
    client.post('/api/defects', json={'project_id':1, 'title':'B', 'priority':'medium', 'status':'closed'}, headers=H(client))
    code, data = j(client.get('/api/reports/summary', headers=H(client)))
    assert code == 200 and data['total'] >= 2 and any(x['status']=='new' for x in data['by_status'])
