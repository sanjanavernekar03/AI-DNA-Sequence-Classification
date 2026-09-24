import os
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client

def test_dark_mode_image_css_rules():
    css_path = os.path.join('app', 'static', 'css', 'style.css')
    assert os.path.exists(css_path)
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
        
    # Check Welcome Page DNA image dark mode rule
    assert '.welcome-dna-img' in css
    assert 'mix-blend-mode: lighten' in css
    
    # Check Dashboard background wrapper dark mode rule
    assert '.dashboard-bg-wrapper' in css
    assert 'dna_dashboard_bg.jpg' in css
    assert 'linear-gradient(rgba(15, 23, 42' in css
    
    # Check Login Page left column dark mode rule
    assert '.auth-left-column' in css
    assert 'dna-auth-background.jpg' in css

def test_dark_mode_classes_in_templates(client):
    # Test Welcome page renders welcome-dna-img
    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert 'welcome-dna-img' in html
    
    # Test Login page renders auth-left-column
    res = client.get('/auth/login')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    assert 'auth-left-column' in html
