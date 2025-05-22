import pytest
from src.main import app
from src.validators.query_validator import QueryValidator

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_valid_query(client):
    response = client.post('/api/v1/query', json={
        'database': 'test_db',
        'query': 'SELECT * FROM users'
    })
    assert response.status_code == 200
    
def test_invalid_query(client):
    response = client.post('/api/v1/query', json={
        'database': 'test_db',
        'query': 'DROP TABLE users'
    })
    assert response.status_code == 400