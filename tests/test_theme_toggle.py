import os
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client

def test_theme_toggle_elements_in_html(client):
    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    
    # Check theme.js script tag
    assert 'static/js/theme.js' in html
    
    # Check theme toggle button
    assert 'theme-toggle-btn' in html
    assert 'theme-icon-dark' in html
    assert 'theme-icon-light' in html
    assert 'theme-label' in html
    
    # Verify theme button appears immediately before global-lang-select
    button_pos = html.find('theme-toggle-btn')
    select_pos = html.find('global-lang-select')
    assert button_pos != -1 and select_pos != -1
    assert button_pos < select_pos

def test_theme_css_and_js_files_exist():
    js_path = os.path.join('app', 'static', 'js', 'theme.js')
    css_path = os.path.join('app', 'static', 'css', 'style.css')
    
    assert os.path.exists(js_path)
    assert os.path.exists(css_path)
    
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    assert 'dnaura_theme_preference' in js_content
    assert 'data-theme' in js_content
    assert 'data-bs-theme' in js_content
    assert 'dark-theme' in js_content
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    assert '[data-theme="dark"]' in css_content
    assert '[data-bs-theme="dark"]' in css_content
