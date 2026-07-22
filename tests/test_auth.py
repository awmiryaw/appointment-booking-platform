def test_register_and_get_profile(client):
    response = client.post('/api/auth/register', json={
        'name': 'New User',
        'email': 'new@example.com',
        'password': 'secret123'
    })

    assert response.status_code == 201
    data = response.json()
    assert data['user']['email'] == 'new@example.com'

    profile = client.get('/api/auth/me', headers={
        'Authorization': f"Bearer {data['token']}"
    })

    assert profile.status_code == 200
    assert profile.json()['name'] == 'New User'


def test_login_wrong_password(client):
    response = client.post('/api/auth/login', json={
        'email': 'client@example.com',
        'password': 'wrong'
    })

    assert response.status_code == 401
