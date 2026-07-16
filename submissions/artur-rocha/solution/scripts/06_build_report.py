import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 - Passo 6 (v2): relatorio executivo completo.
Integra: base numerica + fator humano (pesquisa de mercado) + ICP/build-vs-buy +
watchlist + playbook humano com evidencia + acompanhamento da solucao.
Voz: primeira pessoa, SEM travessao. Saida: solution/report.html (auto-contido).
"""
import base64, pandas as pd, os
SOL=os.path.join(_ROOT,'solution')
OUT=f'{SOL}/outputs'
def b64(p):
    with open(p,'rb') as f: return 'data:image/png;base64,'+base64.b64encode(f.read()).decode()
img={n:b64(f'{OUT}/charts/{n}') for n in os.listdir(f'{OUT}/charts') if n.endswith('.png')}

w=pd.read_csv(f'{OUT}/watchlist_top25.csv').head(12)
flagmap={'flag_escalation':'escalação','flag_low_usage':'uso baixo','flag_no_autorenew':'sem auto-renovação',
         'flag_trial':'em trial','flag_lowsat':'satisfação baixa'}
def flags(r):
    fs=[v for k,v in flagmap.items() if r[k]==1]
    return ', '.join(fs) if fs else 'sem sinal'
rows=''.join(
    f"<tr><td class='mono'>{r.account_id}</td><td>{r.account_name}</td><td>{r.industry}</td>"
    f"<td class='num'>${r.mrr_amount:,.0f}</td><td class='num'>${r.arr_amount:,.0f}</td><td>{flags(r)}</td></tr>"
    for _,r in w.iterrows())

HTML=f"""<style>
.rep{{--ink:#0b0b0b;--sec:#52514e;--mute:#8a897f;--line:#e7e6e2;--surf:#fcfcfb;--blue:#2a78d6;--red:#d03b3b;
 max-width:880px;margin:0 auto;padding:48px 28px;background:var(--surf);color:var(--ink);
 font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;line-height:1.6;font-size:16px;}}
.rep h1{{font-size:31px;line-height:1.18;margin:0 0 6px;letter-spacing:-.01em}}
.rep .sub{{color:var(--sec);font-size:15px;margin-bottom:4px}}
.rep h2{{font-size:22px;margin:46px 0 8px;padding-top:22px;border-top:2px solid var(--ink);letter-spacing:-.01em}}
.rep h3{{font-size:17px;margin:24px 0 4px}}
.rep .lead{{font-size:18px}}
.rep .kpis{{display:flex;flex-wrap:wrap;gap:14px;margin:22px 0}}
.rep .kpi{{flex:1 1 150px;border:1px solid var(--line);border-radius:10px;padding:14px 16px;background:#fff}}
.rep .kpi .v{{font-size:26px;font-weight:700;letter-spacing:-.02em}}
.rep .kpi .v.red{{color:var(--red)}} .rep .kpi .v.blue{{color:var(--blue)}}
.rep .kpi .l{{font-size:12.5px;color:var(--sec);margin-top:2px}}
.rep figure{{margin:22px 0;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:#fff}}
.rep figure img{{width:100%;display:block}}
.rep figcaption{{font-size:13px;color:var(--sec);padding:8px 14px;border-top:1px solid var(--line)}}
.rep .callout{{border-left:4px solid var(--blue);background:#f4f8fe;padding:12px 16px;border-radius:0 8px 8px 0;margin:18px 0}}
.rep .callout.warn{{border-color:var(--red);background:#fdf3f3}}
.rep table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:14px 0}}
.rep th,.rep td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
.rep th{{color:var(--sec);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
.rep td.num,.rep th.num{{text-align:right;font-variant-numeric:tabular-nums}}
.rep .mono{{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;color:var(--sec)}}
.rep .rec{{display:flex;gap:14px;margin:14px 0;padding:14px 16px;border:1px solid var(--line);border-radius:10px;background:#fff}}
.rep .rec .n{{flex:0 0 32px;height:32px;border-radius:50%;background:var(--ink);color:#fff;display:flex;
 align-items:center;justify-content:center;font-weight:700}}
.rep .rec .meta{{font-size:12.5px;color:var(--sec);margin-top:5px}}
.rep .tag{{display:inline-block;font-size:11px;background:#eef;color:var(--blue);border-radius:20px;padding:1px 9px;margin:2px 5px 2px 0}}
.rep .src{{color:var(--mute);font-size:12px;line-height:1.7}}
.rep .src a{{color:var(--blue);text-decoration:none}} .rep .src a:hover{{text-decoration:underline}}
.rep sup{{color:var(--blue);font-weight:700;font-size:11px}}
.rep footer{{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mute)}}
.rep ul{{padding-left:22px}} .rep li{{margin:5px 0}}
</style>
<div class="rep">
<div class="sub">RavenStack · Diagnóstico de Retenção · para o CEO</div>
<h1>Por que a RavenStack ainda não sabe por que perde clientes, e o que eu faria sobre isso</h1>
<div class="sub">Preparado por Artur Rocha · base: 5 tabelas, 500 contas + pesquisa de mercado</div>

<div class="kpis">
 <div class="kpi"><div class="v red">$3,06M</div><div class="l">ARR perdido com churn (US$255k MRR/mês)</div></div>
 <div class="kpi"><div class="v">22%</div><div class="l">das contas cancelaram em 2 anos (~12% ao ano)</div></div>
 <div class="kpi"><div class="v blue">0,47 a 0,55</div><div class="l">poder preditivo de 7 modelos sob 2 rótulos (acaso = 0,50)</div></div>
 <div class="kpi"><div class="v">67%</div><div class="l">do faturamento em só 100 contas</div></div>
</div>

<p class="lead">A pergunta que você me fez, “o que está causando o churn?”, não tem resposta nos dados
que a RavenStack coleta hoje. Eu provei isso com estatística: nenhum sinal atual (uso, satisfação,
suporte, plano) prevê quem cancela. E quando fui à literatura do setor, entendi por quê: nesse tipo de
produto, as maiores causas de churn são <strong>humanas e estratégicas</strong> (o champion que sai, a
falta de valor percebido, a decisão de construir a ferramenta internamente), e nenhuma delas deixa
rastro na telemetria.<sup>1,2</sup> O modelo não está quebrado. Ele está olhando a superfície errada.
Neste relatório eu mostro a prova, trago as hipóteses humanas que faltavam, aponto o segmento sob
ameaça, e desenho o que fazer e como medir se funcionou.</p>

<div class="callout"><strong>O que este relatório não faz, de propósito:</strong> eu não invento uma
causa-raiz confortável. Testei as hipóteses óbvias (uso baixo, satisfação, suporte) e os dados as
rejeitam. Prefiro te entregar um diagnóstico honesto a um bonito e errado, porque um errado custa caro
quando você agir sobre ele.</div>

<h2>1. As três coisas que você acreditava, testadas</h2>
<p>Você me disse: “o churn subiu, mas o CS diz que a satisfação está ok e o produto diz que o uso
cresceu, algo não bate.” Eu testei as três contra os números.</p>
<h3>“O churn subiu”: verdade, e é grave</h3>
<figure><img src="{img['1_churn_trend.png']}"><figcaption>De menos de 5 cancelamentos por mês em 2023 para 117 no fim de 2024. Eu verifiquei se o pico final era efeito do recorte dos dados (que terminam em 31/12): não é, os eventos de dezembro se distribuem pelo mês inteiro e a tendência de alta não depende do último ponto.</figcaption></figure>
<h3>“O uso cresceu”: não se sustenta</h3>
<figure><img src="{img['2_usage_flat.png']}"><figcaption>Uso agregado estagnado em cerca de 10,5 mil eventos por mês o período inteiro. Não há crescimento.</figcaption></figure>
<h3>“A satisfação está ok”: verdade, e é justamente o problema</h3>
<figure><img src="{img['3_satisfaction_blind.png']}"><figcaption>Satisfação de quem ficou (3,96) e de quem cancelou (3,98): diferença de 0,02. O sinal que o CS confia não distingue nada. E 41% dos tickets nem têm nota.</figcaption></figure>
<div class="callout"><strong>O paradoxo, resolvido:</strong> o CS e o Produto não estavam mentindo. Eles
te deram um falso conforto com métricas que não enxergam churn. A satisfação está “ok” porque ela é
cega, e o uso “não caiu” porque uso não prevê saída. Aliás, NPS e CSAT sozinhos preveem só cerca de 31%
dos eventos de churn.<sup>3</sup></div>

<h2>2. Por que ninguém consegue apontar a causa</h2>
<p>Eu construí um modelo de churn com todos os sinais disponíveis e medi sua capacidade de prever quem
cancela, sob dois rótulos diferentes, com validação cruzada.</p>
<figure><img src="{img['4_auc_coinflip.png']}"><figcaption>AUC é o poder preditivo (0,50 é cara-ou-coroa, 1,0 é perfeito). Todos os modelos ficam na linha do acaso.</figcaption></figure>
<p>Coloquei ainda um segundo agente de IA, independente, para tentar refutar o achado, e depois
reproduzi essa verificação em código auditável (<span class="mono">scripts/09_adversarial_verification.py</span>).
O resultado: entre 64 variáveis engenheiradas (uso por funcionalidade, amplitude, tenure, trajetória,
dinâmica de assinaturas), o melhor preditor individual chega a AUC 0,56 e evapora sob correção de
Bonferroni (p=1,0). No teste de permutação, o melhor sinal observado no dataset é <em>mais fraco</em>
que o melhor sinal que o puro acaso gera (p=0,94). E a análise de poder fecha a questão: com esta
amostra, qualquer sinal de AUC 0,59 ou mais teria sido detectado. Ele não existe.</p>
<div class="callout warn"><strong>E há uma descoberta de bastidor grave:</strong> as duas fontes de churn
da empresa se contradizem. A marcação nas contas aponta 110 cancelamentos, a tabela de eventos aponta
352, e elas concordam em apenas 75. A RavenStack não sabe com confiança quem cancelou. E encontrei um terceiro sintoma
do mesmo problema: a tabela de assinaturas nunca encerra registros antigos (todas as 500 contas
aparecem com múltiplas assinaturas “ativas” ao mesmo tempo), o que torna até o MRR da base uma
estimativa em vez de um fato. Pior: os motivos de churn registrados são ficção. O texto livre do cliente tem só 3 frases, e o motivo registrado não
bate com o que o cliente escreveu. Isso não é acaso: no setor, 61% das perdas são indecisão do
comprador e só 14% concorrência direta, então rótulo de saída quase sempre é lixo de dado.<sup>2</sup></div>

<h2>3. O fator humano: as causas que os números não veem</h2>
<p>Se o porquê não está na telemetria, é porque ele é humano. Eu levantei, na literatura do setor, as
causas mais prováveis de churn para um SaaS B2B de colaboração por assento como a RavenStack, e marquei
o que a telemetria consegue ou não ver.</p>
<table>
<thead><tr><th>Causa provável (por tipo de produto)</th><th>Evidência de mercado</th><th>Visível nos dados?</th></tr></thead>
<tbody>
<tr><td><strong>Saída do champion / conta com um único contato</strong></td><td>Champion sai = 51% de churn em 12 meses (65% se for o sponsor). Agir em 48h = +33% de renovação.<sup>1</sup></td><td>Não. É puro sinal humano. Provável causa nº1 do nosso AUC 0,50.</td></tr>
<tr><td><strong>Onboarding falho / não chegou ao valor</strong></td><td>70% do churn nos primeiros 90 dias; só ~37% dos signups ativam; valor em ≤7 dias corta churn ~50%.<sup>4</sup></td><td>Parcial. O produto vê “não ativou”, não vê por que o rollout interno travou.</td></tr>
<tr><td><strong>Valor não realizado / gap de expansão</strong></td><td>Sem expansão, o cliente “cresce para fora” em 18 a 24 meses. Bate com nossos 20% que cancelaram logo após um upgrade.<sup>5</sup></td><td>Parcial. Uso plano mascara a erosão de valor percebido.</td></tr>
<tr><td><strong>Build vs buy com IA (ver seção 4)</strong></td><td>35% das empresas já trocaram um SaaS por ferramenta interna; 78% planejam construir mais.<sup>6</sup></td><td>Não. A conta pode ter uso estável enquanto constrói o substituto.</td></tr>
<tr><td><strong>Contração de assentos / corte de orçamento</strong></td><td>Assentos ociosos são alvo nº1 de corte; orçamento explica 22% das perdas, muito acima da concorrência.<sup>2</sup></td><td>Parcial. A licença mostra a contração, não o motivo humano.</td></tr>
</tbody></table>
<div class="callout">Repare: quase todas as causas dominantes são invisíveis para um modelo treinado
em telemetria. É por isso que o AUC deu 0,50, e é por isso que a solução não é um modelo melhor. É
<strong>cobertura de sinal humano</strong>.</div>

<h2>4. O ICP em risco: build vs buy</h2>
<p>Uma dessas causas merece atenção especial porque é estrutural e emergente: empresas cancelando SaaS
para construir alternativas internas com IA (Claude Code, Cursor, Replit). Mas ela não vale para a base
toda. Ela morde um ICP específico: o cliente com capacidade técnica de construir. Então eu cruzei o
perfil da base com o churn.</p>
<figure><img src="{img['6_icp_devtools.png']}"><figcaption>DevTools tem o maior churn (31%) e as menores contas ($1.702 de MRR médio): é o ICP mais capaz e mais motivado a reconstruir a ferramenta internamente. 58% da base está nos EUA, onde o movimento é mais forte (registro por honestidade: nos dados, o churn dos EUA em si não se destaca do resto do mundo; o sinal geográfico é fraco e o setorial é o que sustenta a hipótese).</figcaption></figure>
<p>O padrão é consistente com a ameaça: o segmento que mais sabe construir é o que mais sai, e é o de
menor ticket, então tem menos a perder ao trocar assinatura por código próprio. <strong>Eu não cravo
que build vs buy é a causa</strong>: estatisticamente o sinal de indústria é apenas direcional (p=0,07),
e a própria literatura traz um contraponto honesto, o de que vibe coding acelera protótipo mas a parte
difícil é o produto, não o código, então boa parte desse movimento volta a comprar.<sup>7</sup> Por
isso a ação certa aqui não é uma conclusão, é uma <strong>conversa estratégica de descoberta</strong>
com as contas DevTools/EUA, perguntando diretamente “vocês estão avaliando construir isto internamente?”,
e defendendo com profundidade de integração e subindo na cadeia de valor (virar sistema de registro, não
uma feature que se reescreve num fim de semana).</p>

<h2>5. Quais contas priorizar</h2>
<p>Como o churn é estatisticamente imprevisível nos dados atuais, eu me recuso a entregar um “score de
risco” por conta. Ele seria ruído com aparência de ciência. Então eu mudo a pergunta de “quem vai
cancelar?” (não dá pra saber) para “o que dói mais se cancelar?” (dá, e muito).</p>
<figure><img src="{img['5_revenue_concentration.png']}"><figcaption>As 100 maiores contas (20% da base) somam 67% do MRR pela assinatura mais recente de cada conta (43% pelo método alternativo; concentrada sob qualquer um). É aqui que a retenção tem alavanca, e onde o toque humano se paga (reter custa 5 a 7x menos que adquirir).</figcaption></figure>
<p>Daí a <strong>watchlist por receita em risco</strong>: contas ativas ordenadas pelo valor que
representam, com sinais fracos de atenção apenas como contexto para a conversa humana, não como
previsão. As 25 primeiras cobrem 35% do MRR ativo.</p>
<table><thead><tr><th>Conta</th><th>Nome</th><th>Setor</th><th class="num">MRR</th><th class="num">ARR</th><th>Sinais de atenção</th></tr></thead><tbody>{rows}</tbody></table>
<div class="src">Top 12 de 25 · lista completa em <span class="mono">outputs/watchlist_full.csv</span>, que acompanha esta entrega como ferramenta.</div>

<h2>6. O que eu faria</h2>
<div class="rec"><div class="n">1</div><div><strong>Consertar o rastreamento de churn e trocar reason codes por entrevistas de saída reais.</strong>
<div class="meta"><span class="tag">Dono: RevOps + CS</span><span class="tag">Esforço: baixo</span><span class="tag">Impacto: base de tudo</span></div>
Reconciliar as duas fontes num único evento de verdade, e substituir o motivo chutado por uma conversa de saída estruturada. É a única forma de corrigir motivos que hoje são ficção. Win-back estruturado recupera cerca de 26% dos churnados.<sup>8</sup></div></div>
<div class="rec"><div class="n">2</div><div><strong>Cobrir o sinal humano nº1: saúde de relacionamento e mapa de champion.</strong>
<div class="meta"><span class="tag">Dono: CS</span><span class="tag">Esforço: médio</span><span class="tag">Impacto: pega o que a telemetria não vê</span></div>
Um health score relacional (não só uso), rastreio de quantos stakeholders ativos cada conta tem, e alerta quando o champion ou o sponsor sai. Health scoring proativo reduz churn cerca de 23%; contas com 3+ stakeholders retêm a 68% vs 23% de contato único.<sup>1,3</sup></div></div>
<div class="rec"><div class="n">3</div><div><strong>Encurtar o tempo até o valor (onboarding).</strong>
<div class="meta"><span class="tag">Dono: Produto + CS</span><span class="tag">Esforço: médio</span><span class="tag">Impacto: ataca 70% do churn (primeiros 90 dias)</span></div>
Definir o marco de valor de cada conta e garantir que ela chegue lá em dias, não meses. É a alavanca de maior retorno comprovado, e hoje só ~18% das empresas definem metas explícitas de onboarding com o cliente.<sup>4</sup></div></div>
<div class="rec"><div class="n">4</div><div><strong>CS “anjo” escalonado por valor, com NPS proativo (não isolado).</strong>
<div class="meta"><span class="tag">Dono: CS/Growth</span><span class="tag">Esforço: médio</span><span class="tag">Impacto: até 35% do MRR sob gestão proativa</span></div>
Toque humano de alto contato nas contas da watchlist (67% do MRR em 100 contas), e NPS automatizado com toque leve na cauda longa. Eu não colocaria anjo humano em 500 contas, senão o custo do concierge passa a receita do cliente pequeno. Isso é “o que automatizar e o que não”. E emparelho o NPS com o health score, porque NPS sozinho prevê pouco.<sup>3</sup>
<br><br><strong>Quanto isso vale, em dólares da RavenStack:</strong> as 100 maiores contas ativas somam
US$731 mil de MRR (US$8,77M de ARR). Com o churn anualizado da base em ~12%, cada ponto percentual de
redução nesse grupo preserva ~US$88 mil de ARR por ano, contra um custo de 2 a 3 CSMs dedicados
(US$150 a 240 mil/ano). A conta completa está em <span class="mono">scripts/10_mrr_robustness_e_cenarios.py</span>:
<table>
<thead><tr><th>Cenário</th><th>Churn do top-100 cai para</th><th class="num">ARR preservado/ano</th><th class="num">Retorno líquido</th></tr></thead>
<tbody>
<tr><td>Conservador</td><td>10% (redução de 2 p.p.)</td><td class="num">$175 mil</td><td class="num">zero a zero</td></tr>
<tr><td>Base</td><td>8% (redução de 4 p.p.)</td><td class="num">$351 mil</td><td class="num">+$111 a 201 mil</td></tr>
<tr><td>Otimista</td><td>6% (redução de 6 p.p.)</td><td class="num">$526 mil</td><td class="num">+$286 a 376 mil</td></tr>
</tbody></table>
Sou transparente: no cenário conservador o programa fica no zero a zero, e a redução assumida vem da
literatura (health scoring proativo reduz churn em ~23%<sup>3</sup>), não desta base. Por isso a seção 7
desenha o teste com grupo de controle antes de escalar o investimento.</div></div>
<div class="rec"><div class="n">5</div><div><strong>EBR com a pergunta de build vs buy, no segmento exposto.</strong>
<div class="meta"><span class="tag">Dono: CS + Vendas</span><span class="tag">Esforço: baixo</span><span class="tag">Impacto: defende o ICP DevTools/EUA</span></div>
Revisão executiva de valor com as contas DevTools/enterprise, perguntando diretamente sobre construção interna, e defendendo com integração profunda e mostrando o custo real de manter software próprio.<sup>6,7</sup></div></div>
<div class="rec"><div class="n">6</div><div><strong>Aposentar as métricas de vaidade do painel.</strong>
<div class="meta"><span class="tag">Dono: CEO/Ops</span><span class="tag">Esforço: baixo</span><span class="tag">Impacto: decisões sobre sinal real</span></div>
Uso agregado e CSAT passivo te deram falso conforto. Enquanto não forem substituídos pelos indicadores das recomendações acima, eu os trataria pelo que são: cegos para churn.</div></div>

<h2>7. Como eu saberia que funcionou</h2>
<p>Você pediu para eu pensar no acompanhamento, e ele é essencial, porque churn é evento raro e atrasado:
esperar 12 meses para saber se algo deu certo é caro demais. Eu separaria as métricas em duas camadas e
testaria as intervenções com controle.</p>
<table>
<thead><tr><th>Camada</th><th>Métricas</th><th>Cadência</th></tr></thead>
<tbody>
<tr><td><strong>Resultado (lagging)</strong></td><td>Churn logo vs churn de receita (sempre separados), GRR e NRR ponderados por receita e por segmento. GRR abaixo de 85% é churn mascarado por expansão.</td><td>Mensal / trimestral</td></tr>
<tr><td><strong>Antecedente (leading)</strong></td><td>Taxa de ativação, tempo até o valor, cobertura de champion (% de contas com 2+ contatos), cobertura de health score, NPS por segmento, retenção D7.</td><td>Semanal / contínua</td></tr>
</tbody></table>
<p><strong>Como testar as intervenções com credibilidade</strong> (com só ~110 churns/ano, o poder
estatístico é baixo): (a) grupo de controle, um recorte aleatório que não recebe a intervenção, e
comparo retenção entre os braços; (b) comparação por coorte, safras antes e depois, olhando a curva de
retenção e não a média; (c) proxies antecedentes, como churn demora, meço primeiro o efeito nos sinais
que comprovadamente preveem churn (ativação, tempo até valor, cobertura de champion), e tenho resposta em
semanas; (d) foco no segmento de maior sinal (topo de receita e DevTools) em vez de diluir na base
toda.<sup>9</sup> Âncora: o benchmark que mais importa é o histórico da própria RavenStack.</p>

<h2>Limitações, e o que eu não afirmo</h2>
<ul>
<li><strong>Eu estou lidando com dado sintético.</strong> A documentação declara geração sintética, e a
ausência de sinal que encontrei é consistente com um churn gerado de forma independente das variáveis.
Eu sustento o achado central (os dados atuais não explicam o churn), mas te peço para ler a magnitude
exata de cada número como ilustrativa, não auditada.</li>
<li><strong>Eu não tenho o porquê real,</strong> e esse é meu ponto: ele não está nos dados. As
recomendações constroem a capacidade de descobri-lo, não fingem que eu já o tenho.</li>
<li><strong>Os valores de MRR são uma estimativa, por culpa do dado.</strong> Como a tabela de assinaturas
nunca encerra registros antigos, eu tive que escolher um método: usei a assinatura mais recente de cada
conta (somar as “ativas” contaria renovações em dobro). Os achados relativos se mantêm sob os dois
métodos (a fatia de receita churnada fica em 20 a 21% nos dois), mas os valores absolutos e a composição
exata da watchlist dependem dessa escolha. Consertar isso é parte da recomendação 1, e a watchlist deve
ser regerada depois desse conserto.</li>
<li><strong>Eu não posso provar, só com esta base, que build vs buy, NPS ou anjos mudam o churn.</strong>
Trago essas hipóteses da pesquisa de mercado e as marco como apostas informadas, justificadas pelo tipo
de produto e pela concentração de receita, e desenho o experimento (seção 7) para você testá-las antes
de escalar.</li>
</ul>

<h2 style="font-size:16px;border-top:1px solid var(--line);color:var(--sec)">Fontes</h2>
<div class="src">
1. Sturdy/ChurnZero e Forecastio (saída de champion, multi-threading), via <a href="https://www.subjolt.com/guides/saas-churn-rate/">Subjolt SaaS Churn Playbook</a> e <a href="https://churnzero.com/blog/multithreading-customer-success/">ChurnZero</a>.<br>
2. Ebsta × Pavilion, 4,2M de oportunidades (indecisão 61% vs concorrência 14%), via <a href="https://www.subjolt.com/guides/saas-churn-rate/">Subjolt</a>; reason codes guarda-chuva: <a href="https://www.linkedin.com/posts/tonysternberg_helping-saas-companies-uncover-the-why-activity-7287457821741195264-sK8-">Tony Sternberg</a>.<br>
3. Totango (health scoring reduz churn ~23%) e NPS isolado prevê ~31%, via <a href="https://www.subjolt.com/guides/saas-churn-rate/">Subjolt</a> e <a href="https://www.planhat.com/customer-success/churn-and-retention">Planhat</a>.<br>
4. Onboarding/ativação/tempo até valor: <a href="https://www.digitalapplied.com/blog/customer-onboarding-time-to-value-2026-saas-metrics-framework">DigitalApplied (Userpilot 37,5%, Amplitude 98%, McKinsey 18%)</a> e <a href="https://www.arcade.software/post/how-to-reduce-customer-churn-b2b-saas">Arcade</a>.<br>
5. Gap de expansão: <a href="https://www.customerscore.io/blog/churn-prediction-in-saas">Customerscore.io</a>; shelfware/assentos: <a href="https://zylo.com/solutions/license-waste">Zylo</a> e <a href="https://www.toriihq.com/articles/saas-management-budget-cuts">Torii</a>.<br>
6. <a href="https://retool.com/blog/ai-build-vs-buy-report-2026">Retool AI Build vs Buy Report 2026 (N=817)</a>.<br>
7. Contraponto ao build vs buy: <a href="https://www.linkedin.com/posts/cagan_build-vs-buy-in-the-age-of-ai-silicon-activity-7363561900757934081-IQMK">Marty Cagan (SVPG)</a> e <a href="https://www.complexsystemspodcast.com/episodes/the-ai-infrastructure-stack-with-jennifer-li-a16z/">a16z/Complex Systems</a>.<br>
8. Win-back ~26%: <a href="https://www.chargebee.com/blog/6-strategies-for-customer-winback-and-reduce-churn/">Chargebee</a>.<br>
9. Leading vs lagging, coortes e controle: <a href="https://esgsuccess.com/fundamentals-basic-leading-and-lagging-indicators-in-customer-success/">ESG Success</a>, <a href="https://www.clientsuccess.com/resources/customer-success-leading-indicators-part-ii">ClientSuccess</a> e <a href="https://amplitude.com/blog/cohorts-to-improve-your-retention">Amplitude</a>. Benchmarks de retenção: <a href="https://www.saas-capital.com/blog-posts/what-is-a-good-retention-rate-for-a-private-saas-company/">SaaS Capital</a>, <a href="https://optif.ai/learn/questions/b2b-saas-net-revenue-retention-benchmark/">Optifai</a>, <a href="https://www.crv.com/content/saas-churn-rate">CRV</a> e <a href="https://chartmogul.com/reports/saas-retention-report/">ChartMogul</a>.
</div>

<footer>Metodologia: join das 5 tabelas em nível de conta, testes de significância (qui-quadrado e
Mann-Whitney), modelos LogReg e RandomForest com validação cruzada 5-fold sob 2 rótulos, verificação
adversarial independente (Bonferroni, permutação, análise de poder), leitura da voz do cliente, e
pesquisa de mercado com fontes do setor. Scripts reproduzíveis em <span class="mono">solution/scripts/</span>.
· Artur Rocha · AI Master Challenge · Julho/2026</footer>
</div>"""

with open(f'{SOL}/report.html','w') as f: f.write(HTML)
assert '—' not in HTML and '–' not in HTML, "AINDA TEM TRAVESSAO!"
print(f"report.html v2 escrito ({len(HTML):,} bytes), {len(img)} graficos, 0 travessoes, 7 secoes")
