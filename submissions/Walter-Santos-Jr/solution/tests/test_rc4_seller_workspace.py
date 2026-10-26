from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'static/index.html').read_text(encoding='utf-8')
JS = (ROOT / 'static/app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/style.css').read_text(encoding='utf-8')

def test_seller_nav_has_three_work_queues():
    for name in ('pipeline', 'rework', 'history'):
        assert f'data-seller-queue="{name}"' in HTML

def test_seller_navigation_requires_identity():
    assert "rc4Persona?.role!=='SELLER'||!rc4Persona.seller" in JS
    assert "setWorkspace(b.dataset.sellerQueue)" in JS

def test_seller_layout_does_not_modify_manager_scope():
    assert 'body[data-persona="seller"] .shell-layout' in CSS
    assert 'body[data-persona="seller"].seller-ready #hierarchyPanel' in CSS

def test_queue_counts_derive_from_api():
    assert "num(d.total)" in JS
    assert "d.jobs.filter(j=>j.status!=='RESOLVED').length" in JS
