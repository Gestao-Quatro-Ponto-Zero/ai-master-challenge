import html
W,H=1180,1240
N={}  # id: (x,y,w,h,shape,label,color,detail)
def node(i,x,y,label,kind='proc',w=230,h=54,detail=''):
    N[i]=dict(x=x,y=y,w=w,h=h,kind=kind,label=label,detail=detail)
C={'proc':('#e8f0fe','#1a73e8'),'dec':('#fff4e5','#e8710a'),'auto':('#e6f4ea','#188038'),'human':('#fce8e6','#c5221f'),'fin':('#f3e8fd','#8430ce'),'log':('#eceff1','#455a64')}
node('E',470,50,'1 · Entrada do chamado<br>(e-mail · chat · telefone · portal · social)',w=300,h=60,detail='Grava created_at e o canal. O relógio de SLA começa aqui (Pilar 3). O D1 não tem esse campo: é a lacuna nº 1.')
node('N',470,140,'2 · NLP / normalização',detail='Minúsculas, sem pontuação e números, remoção de boilerplate de e-mail (38,1% das palavras no D2) e mascaramento de dados pessoais (LGPD).')
node('D',470,245,'3 · Domínio?','dec',w=200,h=80,detail='TI interna × Financeiro/Comercial × Fora do escopo. Motivo: 31,5% do D1 (2.667 tickets) sem categoria de TI correspondente; só 98 das top-300 palavras em comum entre D1 e D2.')
node('F',960,245,'Fila Financeiro/Comercial<br>reembolso · pagamento · entrega<br>cancelamento · recomendação','fin',w=250,h=74,detail='Fora das 8 categorias de TI. Decisão humana (dinheiro, risco de chargeback); a IA só resume e consulta o status.')
node('H',140,450,'Triagem humana<br>(baixa confiança / fora do escopo)','human',w=230,h=64,detail='O humano classifica, e a categoria escolhida vira dado de retreino. Base: pares ambíguos (Hardware × Misc 0,625) e 38 grupos de quase-duplicatas com categorias conflitantes.')
node('C',470,350,'4 · Classificação · 8 categorias TI',w=260,detail='Hardware 28,5% · HR Support 22,8% · Access 14,9% · Misc 14,8% · Storage 5,8% · Purchase 5,2% · Internal Project 4,4% · Admin rights 3,7%. Treino: 47.602 exemplos após limpeza, pesos por categoria, F1-macro. (Ainda não treinado.)')
node('K',470,455,'5 · Confiança?','dec',w=200,h=80,detail='≥ 0,85 → automático · 0,60–0,85 → agente confirma · < 0,60 → triagem humana. Limiares são proposta para calibrar no piloto.')
node('M',790,455,'Agente confirma a sugestão<br>(confiança média)','auto',w=220,h=60,detail='Modo assistido. A correção (se houver) é registrada como category_corrected (KPI 4).')
node('P',470,565,'6 · Priorização<br>impacto × urgência + sinais no texto',w=280,h=60,detail='Por regras auditáveis, porque a prioridade do D1 é aleatória e não serve de rótulo. O humano pode sobrescrever (KPI 15). Crítica nunca vai para autoatendimento.')
node('R',470,660,'7 · Roteamento para a fila',detail='Fila = f(domínio, categoria, prioridade, confiança). Grava queue_initial e o motivo da decisão.')
node('Q',470,770,'8 · Resposta automática<br>possível?','dec',w=220,h=90,detail='Sim só se: categoria elegível (Purchase, Storage, Access-reset) E prioridade diferente de Crítica E confiança alta.')
node('S',470,890,'9 · Autoatendimento<br>reset · fluxo de aprovação · status de PO','auto',w=290,h=60,detail='Purchase: “po” em 70,6% da categoria. Storage: “folder” em 28,8%. Access: “password” 70,8% em Access. Benchmark de sucesso: Gartner, 36% em casos muito simples.')
node('CF',470,1000,'10 · Cliente confirma?','dec',w=210,h=80,detail='Sem resposta: lembrete e fechamento por inatividade com aviso (regra para validar).')
node('A',850,890,'Agente N1<br>com contexto enriquecido','human',w=230,h=60,detail='Recebe texto, categoria, confiança, ação já tentada e histórico. O usuário não repete nada.')
node('N2',850,1000,'Escalonamento N2','human',w=200,h=54,detail='Gatilhos: Crítica, incidente que afeta vários usuários, privilégio de administrador, reabertura, SLA em risco. Motivo registrado.')
node('X',470,1105,'11 · Fechamento + CSAT','auto',w=240,detail='Grava resolved_at e coleta CSAT (a satisfação do D1 é plana e sintética, então é preciso dado real).')
node('L',470,1190,'12 · Registro de resultado → KPIs + retreino (feedback loop)','log',w=430,h=50,detail='Eventos, correções, reaberturas e CSAT alimentam os 17 KPIs e os critérios de retreino (07_riscos.md).')
def box(i):
    n=N[i]; x,y,w,h=n['x'],n['y'],n['w'],n['h']; f,s=C[n['kind']]
    if n['kind']=='dec':
        pts=f"{x},{y-h/2} {x+w/2},{y} {x},{y+h/2} {x-w/2},{y}"; shp=f'<polygon points="{pts}" fill="{f}" stroke="{s}" stroke-width="2"/>'
    else:
        shp=f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="10" fill="{f}" stroke="{s}" stroke-width="2"/>'
    lines=n['label'].split('<br>'); lh=15; y0=y-(len(lines)-1)*lh/2+5
    t=''.join(f'<text x="{x}" y="{y0+k*lh}" text-anchor="middle" class="{"b" if k==0 else "s"}">{html.escape(l)}</text>' for k,l in enumerate(lines))
    return f'<g class="node" data-id="{i}" tabindex="0"><title>{html.escape(n["detail"])}</title>{shp}{t}</g>'
def P(i,side):
    n=N[i]; x,y,w,h=n['x'],n['y'],n['w'],n['h']
    return {'t':(x,y-h/2),'b':(x,y+h/2),'l':(x-w/2,y),'r':(x+w/2,y)}[side]
E=[]
def edge(pts,label='',cls='',lp=None):
    d='M'+' L'.join(f'{a},{b}' for a,b in pts)
    s=f'<path d="{d}" class="e {cls}" marker-end="url(#ar{"_"+cls if cls else ""})"/>'
    if label:
        lx,ly=lp if lp else ((pts[0][0]+pts[1][0])/2,(pts[0][1]+pts[1][1])/2)
        s+=f'<text x="{lx}" y="{ly}" class="el {cls}" text-anchor="middle">{html.escape(label)}</text>'
    E.append(s)
edge([P('E','b'),P('N','t')]); edge([P('N','b'),P('D','t')])
edge([P('D','r'),P('F','l')],'Financeiro/Comercial','',(705,236))
edge([P('D','b'),P('C','t')],'TI interna','',(510,312))
edge([P('D','l'),(140,245),P('H','t')],'Fora do escopo','alt',(250,236))
edge([P('C','b'),P('K','t')])
edge([P('K','l'),P('H','r')],'baixa < 0,60','alt',(312,446))
edge([P('K','r'),P('M','l')],'média','',(623,446))
edge([P('K','b'),P('P','t')],'alta ≥ 0,85','',(515,517))
edge([P('M','b'),(790,565),P('P','r')])
edge([P('H','b'),(140,565),P('P','l')],'classificado','alt',(200,557))
edge([P('P','b'),P('R','t')]); edge([P('R','b'),P('Q','t')])
edge([P('Q','b'),P('S','t')],'Sim','',(490,850))
edge([P('Q','r'),(850,770),P('A','t')],'Não','alt',(660,762))
edge([P('S','b'),P('CF','t')])
edge([P('CF','b'),P('X','t')],'Sim','',(490,1065))
edge([P('CF','r'),(690,1000),(690,890),P('A','l')],'Não','alt',(650,990))
edge([P('A','b'),P('N2','t')],'escala','alt',(885,950))
edge([(N['A']['x']+N['A']['w']/2,890),(1020,890),(1020,1105),P('X','r')],'resolve','',(1050,1000))
edge([P('N2','b'),(850,1090),(N['X']['x']+N['X']['w']/2,1090)],'resolve','',(800,1083))
edge([P('F','r'),(1120,245),(1120,1120),(N['X']['x']+N['X']['w']/2,1120)],'decisão humana','fin',(1120,700))
edge([P('X','b'),P('L','t')])
edge([P('L','l'),(30,1190),(30,350),P('C','l')],'retreino / recalibração','loop',(95,800))
svg=f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Fluxograma do chamado">
<defs>{''.join(f'<marker id="ar{s}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for s,c in [('','#5f6368'),('_alt','#c5221f'),('_loop','#455a64'),('_fin','#8430ce')])}</defs>
{''.join(E)}{''.join(box(i) for i in N)}</svg>'''
import json
det={i:dict(t=n['label'].replace('<br>',' '),d=n['detail']) for i,n in N.items()}
page=f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluxograma do Chamado · Redesign de Suporte com IA</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#fafafa;color:#202124}}
header{{padding:18px 28px;background:#fff;border-bottom:1px solid #e0e0e0}}
h1{{font-size:20px;margin:0 0 4px}} header p{{margin:0;font-size:13px;color:#5f6368}}
.wrap{{display:flex;gap:18px;padding:18px 28px;align-items:flex-start}}
.chart{{flex:1;background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:8px;min-width:0}}
svg{{width:100%;height:auto}}
.e{{fill:none;stroke:#5f6368;stroke-width:2}} .e.alt{{stroke:#c5221f;stroke-dasharray:6 4}} .e.loop{{stroke:#455a64;stroke-dasharray:3 4}} .e.fin{{stroke:#8430ce;stroke-dasharray:6 4}}
.el{{font-size:12px;fill:#3c4043;font-weight:bold;paint-order:stroke;stroke:#fff;stroke-width:4px}} .el.alt{{fill:#c5221f}} .el.loop{{fill:#455a64}} .el.fin{{fill:#8430ce}}
.b{{font-size:13px;font-weight:bold;fill:#202124}} .s{{font-size:11.5px;fill:#3c4043}}
.node{{cursor:pointer}} .node:hover rect,.node:hover polygon,.node.sel rect,.node.sel polygon{{stroke-width:4;filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))}}
aside{{width:300px;position:sticky;top:12px}}
.card{{background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:14px;margin-bottom:12px;font-size:13px;line-height:1.45}}
.card h2{{font-size:14px;margin:0 0 8px}} .lg span{{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;margin-right:6px;border:2px solid}}
.lg div{{margin:4px 0}} .ln{{display:inline-block;width:26px;border-top:2px solid #5f6368;vertical-align:middle;margin-right:6px}}
@media(max-width:900px){{.wrap{{flex-direction:column}} aside{{width:auto;position:static}}}}
</style></head><body>
<header><h1>Como um chamado percorre o sistema · Redesign de Suporte com IA</h1>
<p>Desafio 002 · Fase 3 · Leonardo Candido Lopes · Proposta de desenho (nenhum modelo foi treinado). Clique ou passe o mouse nos blocos para ver os detalhes e a evidência nos dados.</p></header>
<div class="wrap"><div class="chart">{svg}</div>
<aside><div class="card" id="det"><h2>Detalhe da etapa</h2><div id="dt">Clique em um bloco do fluxograma.</div></div>
<div class="card lg"><h2>Legenda</h2>
<div><span style="background:#e8f0fe;border-color:#1a73e8"></span>Processo automático (Pilar 1)</div>
<div><span style="background:#fff4e5;border-color:#e8710a"></span>Decisão</div>
<div><span style="background:#e6f4ea;border-color:#188038"></span>Autoatendimento / assistido (Pilar 2)</div>
<div><span style="background:#fce8e6;border-color:#c5221f"></span>Humano insubstituível</div>
<div><span style="background:#f3e8fd;border-color:#8430ce"></span>Fila Financeiro/Comercial (fora das 8 categorias de TI)</div>
<div><span style="background:#eceff1;border-color:#455a64"></span>Registro / Pilar 3</div>
<div><i class="ln"></i>Caminho principal</div>
<div><i class="ln" style="border-top:2px dashed #c5221f"></i>Caminho alternativo (humano)</div>
<div><i class="ln" style="border-top:2px dotted #455a64"></i>Feedback loop</div></div>
<div class="card"><h2>Regras-chave (propostas)</h2>Limiares de confiança 0,85 / 0,60 a calibrar no piloto · Crítica nunca vai para autoatendimento · Fila Financeiro/Comercial sempre com decisão humana · Todo evento tem timestamp validado.</div></aside></div>
<script>
const D={json.dumps(det,ensure_ascii=False)};
document.querySelectorAll('.node').forEach(g=>{{const f=()=>{{document.querySelectorAll('.node').forEach(x=>x.classList.remove('sel'));g.classList.add('sel');const d=D[g.dataset.id];document.getElementById('dt').innerHTML='<b>'+d.t+'</b><br><br>'+d.d;}};g.addEventListener('click',f);g.addEventListener('mouseenter',f);g.addEventListener('keydown',e=>{{if(e.key==='Enter')f();}});}});
</script></body></html>'''
open('/home/ubuntu/g4_challenge/fase3/04_fluxograma.html','w').write(page); print('ok')
