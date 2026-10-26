from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')
HTML=(ROOT/'static/index.html').read_text(encoding='utf-8')

def test_manager_controls_padding():
    assert '#managerRegionButtons .head-region-button' in CSS
    assert '#managerPicker .head-region-button' in CSS
    assert 'min-height:46px;padding:11px 15px' in CSS

def test_head_aside_border_and_padding():
    assert '#headManagerAside {border:0!important;box-shadow:none!important;}' in CSS
    assert '#headManagerButtons .head-manager-button' in CSS

def test_ownership_removed_from_visible_workspaces():
    assert 'MANAGER / HEAD · OWNERSHIP' not in HTML
    assert '#rc4ManagerPanel {display:none!important;}' in CSS
