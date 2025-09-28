def test_flow_create_defect_and_change_status(client):
    headers = {'Authorization': f'Bearer {client.token}'}

    # 1) создать дефект
    r = client.post('/api/defects', json={'title':'Протечка','project_id':1,'priority':'high'}, headers=headers)
    assert r.status_code == 201, r.data
    defect_id = r.get_json()['id']

    # 2) сменить статус
    r = client.patch(f'/api/defects/{defect_id}', json={'status':'in_review'}, headers=headers)
    assert r.status_code == 200, r.data

    # 3) отфильтровать
    r = client.get('/api/defects?status=in_review', headers=headers)
    assert r.status_code == 200
    assert any(d['id']==defect_id for d in r.get_json())
