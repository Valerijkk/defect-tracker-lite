import os, tempfile, json
import pytest
from app import app, db, User, Project, Defect, generate_password_hash

@pytest.fixture()
def client():
    fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        # seed users
        from werkzeug.security import generate_password_hash
        db.session.add_all([
            User(email='admin@example.com', password_hash=generate_password_hash('admin123'), role='manager'),
            User(email='eng@example.com', password_hash=generate_password_hash('eng123'), role='engineer'),
        ])
        db.session.add(Project(name='P1', description=''))
        db.session.commit()
    with app.test_client() as c:
        yield c
    os.close(fd); os.unlink(db_path)

def j(c, resp): return resp.status_code, json.loads(resp.data)

def login(c, email, password):
    return j(c, c.post('/api/auth/login', json={'email': email, 'password': password}))

def auth_hdr(token): return {'Authorization': 'Bearer ' + token}

def test_health(client):
    code, data = j(client, client.get('/api/health'))
    assert code == 200 and data['status'] == 'ok'

def test_login_ok_and_bad(client):
    code, data = login(client, 'admin@example.com', 'admin123')
    assert code == 200 and 'token' in data
    code2, _ = login(client, 'admin@example.com', 'nope')
    assert code2 == 401

def test_projects_role_access(client):
    # engineer cannot POST /projects
    _, l = login(client, 'eng@example.com', 'eng123')
    r = client.post('/api/projects', json={'name':'X'}, headers=auth_hdr(l['token']))
    assert r.status_code == 403
    # manager can
    _, m = login(client, 'admin@example.com', 'admin123')
    r2 = client.post('/api/projects', json={'name':'X'}, headers=auth_hdr(m['token']))
    assert r2.status_code == 201

def test_defect_create_and_filters(client):
    _, m = login(client, 'admin@example.com', 'admin123')
    h = auth_hdr(m['token'])
    # create few defects
    client.post('/api/defects', json={'project_id':1, 'title':'Leak', 'priority':'high'}, headers=h)
    client.post('/api/defects', json={'project_id':1, 'title':'Crack', 'priority':'low'}, headers=h)
    # filter by q and priority
    code, data = j(client, client.get('/api/defects?q=Leak&priority=high', headers=h))
    assert code == 200 and len(data) == 1 and data[0]['title'] == 'Leak'

def test_report_summary(client):
    _, m = login(client, 'admin@example.com', 'admin123')
    h = auth_hdr(m['token'])
    client.post('/api/defects', json={'project_id':1, 'title':'A', 'priority':'high', 'status':'new'}, headers=h)
    client.post('/api/defects', json={'project_id':1, 'title':'B', 'priority':'medium', 'status':'closed'}, headers=h)
    code, data = j(client, client.get('/api/reports/summary', headers=h))
    assert code == 200 and data['total'] >= 2 and any(x['status']=='new' for x in data['by_status'])
