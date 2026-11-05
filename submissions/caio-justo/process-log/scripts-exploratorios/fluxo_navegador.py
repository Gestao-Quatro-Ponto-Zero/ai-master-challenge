import sys,json,urllib.request
from playwright.sync_api import sync_playwright
B='http://localhost:8765'; out=sys.argv[1]; erros=[]
with sync_playwright() as p:
    b=p.chromium.launch(channel='chrome'); c=b.new_context(viewport={'width':1280,'height':860}); g=c.new_page()
    g.on('console',lambda m: erros.append(m.text) if m.type=='error' and 'font' not in m.text.lower() else None); g.on('pageerror',lambda e: erros.append(str(e)))
    g.goto(B+'/'); g.wait_for_selector('#foco .deal'); g.screenshot(path=out+'/01-minha-semana.png')
    print('foco',g.locator('#foco .deal').count(),'checar',g.locator('#checar .deal').count()); print(g.locator('#foco .deal').first.inner_text()[:300])
    pri=g.locator('#foco .deal').first.get_attribute('data-id'); nome=g.locator('#foco .deal').first.locator('.deal-nome').inner_text()
    g.locator('#foco .deal').first.locator('button[data-acao=adiar]').click(); g.wait_for_selector('.toast:not([hidden])'); g.wait_for_timeout(300); print('adiar → first agora',g.locator('#foco .deal').first.get_attribute('data-id')!=pri)
    g.locator('#checar .deal').first.scroll_into_view_if_needed(); ch=g.locator('#checar .deal').first; cid=ch.get_attribute('data-id'); ch.locator('button[data-valor=vivo]').click(); g.wait_for_timeout(400)
    print('pressed',g.locator(f'#checar .deal[data-id="{cid}"] button[data-valor=vivo]').get_attribute('aria-pressed')); print('contagem',g.locator('#checar').evaluate('e=>e.previousElementSibling.innerText'))
    g.locator(f'#checar .deal[data-id="{cid}"]').scroll_into_view_if_needed(); g.screenshot(path=out+'/02-confirmar-parados.png')
    g.goto(B+'/?tela=head'); g.wait_for_selector('.medidas'); g.screenshot(path=out+'/03-visao-head-real.png',full_page=True); print('real checagem',g.locator('.leitura').first.inner_text()[:220].replace('\n',' | '))
    g.select_option('#regiao','East'); g.wait_for_timeout(500); print('url',g.url,'parados East',g.locator('.medida .valor').nth(1).inner_text())
    g.goto(B+'/?tela=head&modo=demo'); g.wait_for_selector('#simulador'); g.locator('#simulador button.primario').click(); g.wait_for_timeout(700); g.screenshot(path=out+'/04-visao-head-demonstracao.png',full_page=True); print('demo',g.locator('.leitura').nth(0).inner_text()[:320].replace('\n',' | ')); print('demo2',g.locator('.leitura').nth(1).inner_text()[:320].replace('\n',' | ')); print('aviso visivel',g.locator('#aviso-demo').is_visible())
    g.goto(B+'/?tela=head'); g.wait_for_selector('.medidas'); print('real segue limpo',g.locator('.leitura').first.inner_text().split('\n')[2:4])
    m=b.new_context(viewport={'width':390,'height':844}).new_page(); m.goto(B+'/?tela=semana&vendedor=Darcel%20Schlecht'); m.wait_for_selector('#qualificar .deal'); m.screenshot(path=out+'/05-celular-sem-ativos.png'); print('overflow mobile',m.evaluate('document.documentElement.scrollWidth>innerWidth'))
    g.goto(B+'/api/semana?vendedor=Ninguem'); print('erro api',g.inner_text('body')[:60])
    print('ERROS',erros); b.close()
