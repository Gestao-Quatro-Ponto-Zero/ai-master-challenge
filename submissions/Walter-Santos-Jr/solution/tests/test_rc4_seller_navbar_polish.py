from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'static/index.html').read_text(encoding='utf-8')
CSS=(ROOT/'static/style.css').read_text(encoding='utf-8')

def test_queue_controls_appear_before_regions():
    nav=HTML.split('id="sellerExecutionNav"',1)[1].split('</section>',1)[0]
    assert 'MINHA CARTEIRA' not in nav
    assert nav.index('data-seller-queue="pipeline"') < nav.index('id="sellerRegionButtons"')

def test_queue_buttons_have_no_icons():
    nav=HTML.split('id="sellerExecutionNav"',1)[1].split('</section>',1)[0]
    group=nav.split('class="seller-queue-buttons"',1)[1].split('</div>',1)[0]
    assert '↗' not in group and '<svg' not in group and '<i ' not in group

def test_manager_and_queue_heights_align():
    assert 'min-height: 46px' in CSS
    assert 'seller-nav-stack .head-manager-button' in CSS
