const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = n => Number(n).toLocaleString('pt-BR');
const actionNames = {IDENTIFY_ACCOUNT:'Identificar conta', QUALIFY_OPPORTUNITY:'Qualificar oportunidade',REVIEW_ENGAGEMENT:'Revisar engajamento',RESOLVE_QUALIFICATION_BLOCKER:'Resolver bloqueio de qualificação'};
const state = {workspace:"pipeline",page:1,pages:1,filters:{},selected:null,jobHistory:false,jobCategory:"data",jobOrder:[],jobCache:new Map(),jobBusy:false,reworkPage:1,reworkPageSize:6,workspaceRequest:0,detailRequest:0,dealOrder:[],dealRows:new Map(),refreshing:false,queuedRefresh:false,filterTimer:null};
const filterIds = {stage:'deal_stage',agent:'sales_agent',manager:'manager',region:'regional_office',band:'priority_band',search:'search'};
async function api(path,options={}) {const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);try{const response=await fetch(path,{...options,signal:controller.signal});const body=await response.json();if(!response.ok)throw Error(body.error||'Falha na requisição');return body;}catch(e){if(e.name==='AbortError')throw Error('Tempo limite de 15 segundos excedido. Verifique a conexão com o backend e recarregue as filas.');throw e;}finally{clearTimeout(timeout);}}
function selectOptions(id, values){const el=$(id);values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;el.appendChild(o);});}
function currentParams(){const params=new URLSearchParams();Object.entries(filterIds).forEach(([id,key])=>{const value=$(id).value.trim();if(value)params.set(key,value)});params.set('page',state.page);params.set('page_size',8);return params.toString();}
function dealCard(r){const id=String(r.opportunity_id);const active=state.selected===id;
return `<button type="button" class="opportunity-card ${active?'selected':''}" data-deal="${esc(id)}" aria-pressed="${active}" aria-label="Abrir oportunidade ${esc(id)}"><span class="opportunity-card-top"><strong class="deal-id">${esc(id)}</strong><span class="pill ${esc(r.priority_band)}">${esc(r.priority_band)}</span></span><span class="opportunity-card-account">${esc(r.account||'Conta não identificada')}</span><span class="opportunity-card-product">${esc(r.product_normalized)} · ${esc(r.deal_stage)}</span><span class="opportunity-card-meta">${esc(r.sales_agent)} · ${esc(r.regional_office)}</span><span class="opportunity-card-bottom"><span><small>Índice de prioridade</small><b>${Number(r.priority_score).toFixed(1)}<small> /100</small></b></span><span class="opportunity-card-action">${esc(actionNames[r.next_best_action]||r.next_best_action)}</span></span></button>`;}
function renderOpportunityCards(){const target=$('opportunityCards');if(!target)return;
 const cards=state.dealOrder.map(id=>state.dealRows.get(id)).filter(Boolean);
 target.innerHTML=cards.length?cards.map(dealCard).join(''):'<p class="empty-jobs">Nenhuma oportunidade encontrada nesta seleção.</p>';
 target.querySelectorAll('[data-deal]').forEach(b=>b.onclick=()=>openDetail(b.dataset.deal));
}
function renderAsideDeals(){const el=$("asideDealCards");if(!el)return;const rows=state.dealOrder.map(id=>state.dealRows.get(id)).filter(Boolean);el.innerHTML=rows.length?rows.map(r=>`<button type="button" class="aside-deal ${state.selected===String(r.opportunity_id)?"selected":""}" data-aside-deal="${esc(r.opportunity_id)}"><strong>${esc(r.opportunity_id)}</strong><span>${esc(r.account||"Conta não identificada")}</span><small>${esc(r.product_normalized)} · ${esc(r.deal_stage)}</small><b>${Number(r.priority_score).toFixed(1)} / 100</b></button>`).join(""):"<p>Nenhuma oportunidade neste filtro.</p>";el.querySelectorAll("[data-aside-deal]").forEach(b=>b.onclick=()=>openDetail(b.dataset.asideDeal));}
function markSelectedDeal(){renderAsideDeals();const target=$('opportunityCards');if(!target)return;target.querySelectorAll('[data-deal]').forEach(b=>{const active=b.dataset.deal===state.selected;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});}
function scheduleRefresh(){if(state.filterTimer)clearTimeout(state.filterTimer);state.filterTimer=setTimeout(()=>{state.page=1;state.dealOrder=[];state.selected=null;refresh();},220);}
async function refresh(){if(state.refreshing){state.queuedRefresh=true;return;}state.refreshing=true;try{const d=await api('/api/dashboard?'+currentParams());state.pages=d.pages;state.page=d.page;
await renderRevopsAnalytics();
$('totalLabel').textContent=num(d.total)+' oportunidades';$('pageInfo').textContent=`Página ${d.page} de ${d.pages}`;$('prev').disabled=d.page===1;$('next').disabled=d.page===d.pages;
// Stable deal-card identity: preserve existing order while a deal is selected.
const incoming=d.rows.map(r=>String(r.opportunity_id));
state.dealRows=new Map(d.rows.map(r=>[String(r.opportunity_id),r]));
if(!state.selected || !state.dealOrder.length){state.dealOrder=incoming;}
else {const keep=state.dealOrder.filter(id=>state.dealRows.has(id));state.dealOrder=[...keep,...incoming.filter(id=>!keep.includes(id))];}
renderAsideDeals();
if(rc4Persona?.role==='SELLER'&&rc4Persona.seller){$('sellerPipelineCount').textContent=num(d.total);}
await refreshJobs();
sellerNavSync();
if(!state.selected && state.workspace==='pipeline')selectWorkspaceFirst('pipeline');
if(!state.optionsLoaded){selectOptions('agent',d.options.sales_agent);selectOptions('manager',d.options.manager);selectOptions('region',d.options.regional_office);state.optionsLoaded=true;}
}catch(e){toast('Erro ao carregar dados: '+e.message,'error')}finally{state.refreshing=false;if(state.queuedRefresh){state.queuedRefresh=false;refresh();}}}

// V4.5-C: source-qualified RevOps intelligence. Never synthesize unavailable Won/Lost or revenue.
let analyticsCache=null;
let activeTrendKey=null;
const expandIcon="↗";
const collapseIcon=`<svg viewBox="0 0 32 32" width="19" height="19" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"><path d="M29 3 L18 14 M18 5 L18 14 L27 14"/><path d="M3 29 L14 18 M5 18 L14 18 L14 27"/></svg>`;
function syncTrendButtons(){document.querySelectorAll("[data-kpi]").forEach(b=>{const open=activeTrendKey===b.dataset.kpi&&!$("trendPanel").hidden;b.innerHTML=open?collapseIcon:expandIcon;b.setAttribute("aria-expanded",String(open));b.setAttribute("aria-label",(open?"Recolher gráfico de ":"Abrir gráfico de ")+b.dataset.label);b.title=(open?"Recolher":"Abrir")+" gráfico de "+b.dataset.label;});}
function closeTrend(){activeTrendKey=null;$("trendPanel").hidden=true;syncTrendButtons();}

async function renderRevopsAnalytics(){
 const args=new URLSearchParams();for(const [id,key] of Object.entries(filterIds)){if(['agent','manager','region','stage','band'].includes(id)){const el=$(id);if(el?.value)args.set(key,el.value);}}
 try{analyticsCache=await api('/api/revops/analytics?'+args.toString());}catch(e){$('kpis').textContent='Indicadores indisponíveis: '+e.message;return;}
 const m=analyticsCache.metrics;
 const items=[['Oportunidades','opportunities','deals'],['Engaging','engaging','deals'],['Prospecting','prospecting','deals'],['Missing Account','missing_account','deals']];
 // Operational KPIs are current-state counters. No trend control without verified history.
 $('kpis').innerHTML=items.map(([label,key,unit])=>{const val=m[key];const available=val!==null&&val!==undefined;const explanation=analyticsCache.availability[key]||'Fonte indisponível';return `<div class="nav-kpi"><span>${esc(label)}</span><strong>${available?num(val)+(unit?' '+unit:''):'N/D'}</strong>${!available?`<small title="${esc(explanation)}">Fonte indisponível</small>`:''}</div>`;}).join('');
 syncTrendButtons();
 const c=$('conversionSummary');if(c){
   const conv=analyticsCache.conversion;
   if(!conv?.available){c.innerHTML=`<div class="conversion-heading"><strong>Conversão · Won / Lost</strong></div><small>${esc(conv?.reason||'Histórico indisponível')}</small>`;}
   else {
     const pct=conv.win_rate||0;
     const months=conv.series||[];
     const w=210,h=48,pad=5,min=0,max=100,dx=months.length>1?(w-2*pad)/(months.length-1):0;
     const pts=months.map((x,i)=>`${pad+i*dx},${h-pad-x.win_rate/100*(h-2*pad)}`).join(' ');
     c.innerHTML=`<div class="conversion-heading"><strong>Conversão · Won / Lost</strong><button type="button" class="kpi-trend conversion-trend" data-kpi="conversion" data-label="Conversão Won/Lost" aria-expanded="false" aria-label="Abrir gráfico de Conversão Won/Lost">↗</button></div><div class="conversion-body"><div class="conversion-donut" style="--won-percent:${pct}%"><div><b>${num(pct)}%</b><small>Win Rate</small></div></div><div class="conversion-legend"><span><i class="legend-dot won-dot"></i>Won <b>${num(conv.won)}</b></span><span><i class="legend-dot lost-dot"></i>Lost <b>${num(conv.lost)}</b></span></div></div><svg class="conversion-sparkline" viewBox="0 0 ${w} ${h}" role="img" aria-label="Win Rate mensal histórico"><polyline points="${pts}" fill="none" stroke="var(--action-blue,#60a5fa)" stroke-width="2.5" stroke-linejoin="round"/>${months.map((x,i)=>`<circle cx="${pad+i*dx}" cy="${h-pad-x.win_rate/100*(h-2*pad)}" r="2.3" fill="var(--action-blue,#60a5fa)"><title>${esc(x.month)}: ${num(x.win_rate)}% · Won ${num(x.won)} / Lost ${num(x.lost)}</title></circle>`).join('')}</svg><small>Histórico ${esc(conv.period.join(' a '))}</small>`;
     c.querySelector('.conversion-trend').onclick=()=>{if(activeTrendKey==='conversion'&&!$('trendPanel').hidden)closeTrend();else showTrend('conversion');};syncTrendButtons();
   }
 }

}
function showTrend(key){
 if(!analyticsCache)return;
 const panel=$('trendPanel'),title=$('trendTitle'),content=$('trendContent');activeTrendKey=key;panel.hidden=false;positionTrendOverlay();syncTrendButtons();
 const available=key==='conversion'?!!analyticsCache.conversion?.available:(analyticsCache.metrics[key]!==null&&analyticsCache.metrics[key]!==undefined);
 const label={opportunities:'Oportunidades',engaging:'Engaging',prospecting:'Prospecting',missing_account:'Missing Account',qualified:'Qualified',activities:'Atividades',won:'Won',lost:'Lost',revenue:'Revenue',active_customers:'Clientes ativos',new_customers:'Novos clientes'}[key]||key;
 title.textContent=key==='conversion'?'Conversão histórica · Won / Lost':('Evidência temporal · '+label);
 if(!available){content.innerHTML=`<p class="trend-note">${esc(analyticsCache.availability[key]||'Não há série temporal validada para esta métrica.')}</p>`;return;}
 const conversion=key==='conversion';
 if(!conversion){
   const value=analyticsCache.metrics[key];
   const explanation=analyticsCache.series_status?.[key]||'Histórico temporal não disponível.';
   title.textContent='Estado atual · '+label;
   content.innerHTML=`<div class="trend-current-state"><div class="trend-current-value">${num(value)}</div><div class="trend-current-label">${esc(label)} · posição atual</div></div><p class="trend-note">${esc(explanation)} Não foi desenhada uma curva temporal sem dados verificáveis.</p>`;
   return;
 }
 const series=(analyticsCache.conversion.series||[]).map(x=>({month:x.month,value:x.win_rate}));
 const note='Win Rate mensal de Deals encerrados no CRM histórico; NÃO representa conversão atual e não acompanha filtros do Pipeline.';
 if(!series.length){content.innerHTML='<p class="trend-note">Não há fechamentos datados suficientes para construir a série.</p>';return;}
 const w=800,h=160,pad=30,max=100,dx=series.length>1?(w-2*pad)/(series.length-1):0;
 const points=series.map((x,i)=>`${pad+i*dx},${h-pad-(x.value/max)*(h-2*pad)}`).join(' ');
 const labels=series.filter((_,i)=>i===0||i===series.length-1||i%Math.max(1,Math.ceil(series.length/6))===0).map(x=>esc(x.month)).join(' · ');
 content.innerHTML=`<svg viewBox="0 0 ${w} ${h}" class="revops-line" role="img" aria-label="Win Rate mensal: ${esc(labels)}"><line x1="${pad}" y1="${h-pad}" x2="${w-pad}" y2="${h-pad}" stroke="currentColor" opacity=".3"/><polyline points="${points}" fill="none" stroke="var(--action-blue, #60a5fa)" stroke-width="3" stroke-linejoin="round"/>${series.map((x,i)=>`<circle cx="${pad+i*dx}" cy="${h-pad-(x.value/max)*(h-2*pad)}" r="3" fill="var(--action-blue, #60a5fa)"><title>${esc(x.month)}: ${num(x.value)}%</title></circle>`).join('')}</svg><div class="trend-months">${labels}</div><p class="trend-note">${esc(note)}</p>`;
}

function choice(name,value){return `<select name="${name}">${[['unknown','Ainda não informado'],['yes','Confirmado pelo vendedor'],['no','Não confirmado / impedimento']].map(([v,l])=>`<option value="${v}" ${v===value?'selected':''}>${l}</option>`).join('')}</select>`}
function decisionTab(name){return `<button class="decision-tab ${state.decisionTab===name?'active':''}" data-decision-tab="${name}" type="button">${{overview:'Inteligência',qualification:'Qualificação',execution:'Execução',history:'Histórico'}[name]}</button>`;}
function decisionContent(d){const r=d.opportunity,q=r.qualification||{},tab=state.decisionTab||'overview';
 const head=`<div class="decision-head"><div><div class="eyebrow">OPPORTUNITY 360 · ${esc(r.opportunity_id)}</div><h2>${esc(r.account||'Conta não identificada')}</h2><p>${esc(r.product_normalized)} · ${esc(r.sales_agent)} · ${esc(r.regional_office)}</p></div><div class="decision-score"><strong>${r.priority_score.toFixed(1)}<small> / 100</small></strong><span>Índice de priorização · não probabilidade</span></div></div>`;
 const tabs='';
 let content='';
 if(tab==='overview'){
 const colors=['#60a5fa','#2dd4bf','#fbbf24'];
 const gauges=(r.score_explanation||[]).map((c,i)=>{const value=Math.max(0,Math.min(100,Number(c.component)||0));const weight=Number(c.weight)||0;const points=Number(c.points)||0;return `<div class="xai-gauge-card"><div class="xai-gauge-label">${esc(c.label)}</div><svg class="xai-gauge" viewBox="0 0 180 115" role="img" aria-label="${esc(c.label)}: ${value.toFixed(1)} de 100"><path d="M 17 96 A 73 73 0 0 1 163 96" fill="none" stroke="var(--gauge-track)" stroke-width="13" stroke-linecap="round"/><path d="M 17 96 A 73 73 0 0 1 163 96" fill="none" stroke="${colors[i%3]}" stroke-width="13" stroke-linecap="round" pathLength="100" stroke-dasharray="${value} 100"/><text x="90" y="75" text-anchor="middle" class="xai-gauge-value">${value.toFixed(1)}</text><text x="90" y="94" text-anchor="middle" class="xai-gauge-unit">/ 100</text></svg><div class="xai-gauge-weight">Peso ${weight}%</div><div class="xai-gauge-points">+${points.toFixed(1)} pontos</div>${!r.account_known && /conta|account/i.test(c.label)?'<div class="xai-neutral">Porte neutro: dados da conta insuficientes</div>':''}</div>`}).join('');
 const total=(r.score_explanation||[]).reduce((sum,c)=>sum+Number(c.points||0),0);
 content=`<div class="decision-stats compact"><span>Estágio: <b>${esc(r.deal_stage)}</b></span><span>Produto: <b>${esc(r.product_normalized)}</b></span><span>Prioridade: <b>${esc(r.priority_band)}</b></span></div><section class="xai-panel"><div class="xai-panel-title"><h3>Explainable AI · Composição do score</h3><span>Índice baseado em regras</span></div><div class="xai-gauge-grid">${gauges}</div><div class="xai-score-progress" role="group" aria-label="Deal Score em escala de 0 a 100 pontos"><div class="xai-score-progress-heading"><strong>Potencial do deal · índice de priorização</strong><span>${Math.max(0,Math.min(100,total)).toFixed(1)} / 100 pts</span></div><div class="xai-score-progress-track" role="progressbar" aria-label="Deal Score V3" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.max(0,Math.min(100,total)).toFixed(1)}"><div class="xai-score-progress-fill" style="width:${Math.max(0,Math.min(100,total)).toFixed(2)}%"></div></div><div class="xai-score-progress-axis"><span>0</span><span>25</span><span>50</span><span>75</span><span>100</span></div></div><div class="xai-total"><span>Contribuições ponderadas: ${(r.score_explanation||[]).map(c=>Number(c.points||0).toFixed(1)).join(' + ')} = <strong>${total.toFixed(1)} pontos</strong></span><small>Não representa probabilidade de fechamento. Preço de catálogo não é valor negociado.</small></div></section><section class="xai-next-action"><h3>Next Best Action</h3><div class="nba-content-row"><div class="nba-description"><strong>${esc(actionNames[r.next_best_action]||r.next_best_action)}</strong><p>${esc(r.explanation||'')}</p></div><div class="nba-actions"><button type="button" class="primary" id="executeNBA">Executar ação ↗</button><button type="button" class="outline" id="salesHistoryBtn">Histórico de atividades</button></div></div></section>`;
 }
 if(tab==='qualification')content=`<h3>Qualificação comercial · ${esc(r.opportunity_id)}</h3><p>Registre somente informações conhecidas. Não informado é um estado válido; os registros não alteram o Deal Score.</p><form id="qualForm"><label>Contato com responsável pela decisão ${choice('decision_maker',q.decision_maker||'unknown')}</label><label>Prazo de compra ${choice('timeline',q.timeline||'unknown')}</label><label>Disponibilidade de orçamento ${choice('budget',q.budget||'unknown')}</label><label>Contexto e evidências comerciais<textarea name="notes" maxlength="1000" rows="4" placeholder="Registre nomes, datas, valores e fontes confirmadas quando disponíveis.">${esc(q.notes||'')}</textarea></label><button class="primary" type="submit">Salvar informações comerciais</button><div class="feedback" id="qualFeedback"></div></form><p class="qualification-disclaimer">Os três campos de situação utilizam a política operacional existente. Uma futura evolução poderá substituí-los por informações estruturadas de contatos, valores e datas.</p>`;
 if(tab==='execution')content=`${!r.account_known?`<section class="account-evidence"><h3>Rework · Identificar conta</h3><p>Informe a conta real associada ao Deal. A validação cadastral local ocorre ao salvar.</p><form id="accountForm"><label>Conta do cliente<input name="account" maxlength="120" required placeholder="Nome da conta no CRM" /></label><button class="primary" type="submit">Salvar conta e verificar</button><div class="feedback" id="accountFeedback"></div></form></section>`:`<p class="account-confirmed">Conta identificada: <strong>${esc(r.account)}</strong></p>`}<h3>Closed-Loop · Jobs desta oportunidade</h3><p>Visualizar um deal não inicia automaticamente uma tarefa. Use a ação explícita abaixo para registrar o início da execução.</p>${d.jobs.map(j=>`<div class="job-card job-status-${esc(j.status)}"><div class="job-card-top"><b>JOB #${j.id} · ${esc(actionNames[j.job_type]||j.job_type)}</b><span class="job-state">${esc(j.status)}</span></div><p>${esc(j.priority)} · ${esc(j.job_type)}</p><p class="evidence-guidance">${esc(j.evidence_hint||'')}</p><div class="job-actions">${jobButtons(j)}</div></div>`).join('')||'<p>Nenhum job associado.</p>'}<h3>Registrar atividade</h3><form id="actForm"><label>Ação<select name="action"><option value="CONTACT">Contato realizado</option><option value="QUALIFY">Qualificação</option><option value="REVIEW">Revisão do deal</option><option value="FOLLOW_UP">Follow-up</option><option value="OTHER">Outra ação</option></select></label><label>Observação<textarea name="note" maxlength="1000" rows="2" placeholder="O que foi feito?"></textarea></label><button class="primary" type="submit">Registrar ação</button><div class="feedback" id="actFeedback"></div></form>`;
 if(tab==='history')content=`<h3>Histórico de atividades</h3>${d.activities.length?d.activities.map(a=>`<div class="activity"><b>${esc(a.action)}</b> · ${esc(a.note||'Sem observação')}<small>${esc(a.created_at)}</small></div>`).join(''):'<p>Nenhuma atividade registrada.</p>'}<h3>Histórico do Closed-Loop</h3>${d.jobs.flatMap(j=>(j.events||[]).map(e=>`<div class="activity"><b>Job #${j.id} · ${esc(e.event_type)}</b><small>${esc(e.created_at)}</small><p>${esc(e.note||'')}</p></div>`)).join('')||'<p>Nenhum evento registrado.</p>'}`;
 return head+tabs+`<div class="decision-body">${content}</div>`;
}
// V4.5-B.1: Rework is a job-centric workspace, never the commercial execution tab.
function selectedReworkJob(){return state.jobCache.get(String(state.selectedReworkJob||''));}
function reworkDetail(d, selectedJob){
 const r=d.opportunity,j=selectedJob;
 if(!j||String(j.opportunity_id)!==String(r.opportunity_id))return '<div class="decision-empty"><h2>Selecione uma pendência no Aside</h2></div>';
 const events=(d.jobs.find(x=>String(x.id)===String(j.id))?.events||[]);
 const history=events.slice(0,8).map(e=>`<div class="rework-event"><strong>${esc(e.event_type)}</strong><span>${esc(e.created_at)}</span><p>${esc(e.note||'')}</p></div>`).join('');
 const confirmed=state.reworkConfirmation&&String(state.reworkConfirmation.jobId)===String(j.id);
 const currentScore=Number(r.priority_score).toFixed(1);
 const scoreCard=`<div class="rework-score-trace"><strong>Deal Score V3: ${currentScore} / 100</strong><small>Índice de priorização, não probabilidade de fechamento. O Quality Gate bloqueia a execução comercial até a correção.</small></div>`;
 const trace=d.score_trace;
 const verifiedScore=trace?`<div class="rework-score-trace"><strong>Score antes: ${Number(trace.score_before).toFixed(1)} / 100 · Score após: ${Number(trace.score_after).toFixed(1)} / 100 · Variação: ${(Number(trace.score_after)-Number(trace.score_before)).toFixed(1)} ponto(s)</strong><small>${esc(trace.calculation_note)} A posição no Pipeline segue o score vigente.</small></div>`:scoreCard;
 if(confirmed)return `<section class="rework-workspace rework-success" role="status"><div class="eyebrow">DATA REWORK · JOB #${j.id} · DEAL ${esc(r.opportunity_id)}</div><h2>✓ VERIFIED · Correção concluída</h2>${verifiedScore}<p>Conta <strong>${esc(r.account)}</strong> registrada. Quality Gate aprovado; Deal liberado ao Pipeline.</p><p>Validação cadastral local, sem consulta a cadastro mestre externo.</p><button type="button" class="primary" id="nextRework">Próxima pendência →</button><h3>Rastreabilidade</h3>${history||'<p>Eventos registrados no backend.</p>'}</section>`;
 if(j.job_type!=='IDENTIFY_ACCOUNT')return `<section class="rework-workspace"><div class="eyebrow">DATA REWORK · JOB #${j.id} · DEAL ${esc(r.opportunity_id)}</div><h2>${esc(actionNames[j.job_type]||j.job_type)}</h2><p>Esta pendência é de qualificação comercial, não de correção cadastral. Utilize a área de Qualificação do Pipeline para registrar evidências.</p><div class="rework-guidance">${esc(j.evidence_hint||'')}</div><h3>Histórico do job</h3>${history||'<p>Sem eventos adicionais.</p>'}</section>`;
 return `<section class="rework-workspace"><div class="eyebrow">DATA REWORK · JOB #${j.id} · DEAL ${esc(r.opportunity_id)}</div><h2>Identificar conta</h2>${scoreCard}<div class="rework-guidance">Defeito bloqueante: MISSING_ACCOUNT. Informe a conta real associada ao Deal e valide a correção.</div><div class="rework-status">Estado atual: <strong>${esc(j.status)}</strong> · Quality Gate: BLOCKED</div><form id="accountForm"><label>Conta do cliente<input name="account" maxlength="120" required placeholder="Nome da conta no CRM" autocomplete="off" /></label><button class="primary" type="submit">Salvar e verificar</button><div class="feedback" id="accountFeedback" role="alert"></div></form><p class="rework-disclaimer">Verificação local de presença e formato; não comprova a identidade em um cadastro externo.</p><h3>Histórico do job</h3>${history||'<p>Correção ainda não registrada.</p>'}</section>`;
}
async function nextRework(){state.reworkConfirmation=null;await refreshJobs();if(state.workspace==='rework')await selectWorkspaceFirst('rework');}
async function openDetail(id,keepTab=false,requestedJobId=null){
 if(salesModalDeal&&salesModalDeal!==id)closeSalesAction();
 const detailRequest=++state.detailRequest;
 const requestedWorkspace=state.workspace;
 const jobId=requestedWorkspace==='rework'?String(requestedJobId??state.selectedReworkJob??''):null;
 try{if(!keepTab||state.selected!==id)state.decisionTab=workspaceToDecisionTab(state.workspace);const d=await api('/api/opportunities/'+encodeURIComponent(id));if(detailRequest!==state.detailRequest||requestedWorkspace!==state.workspace)return;
 if(requestedWorkspace==='rework'&&jobId!==String(state.selectedReworkJob??''))return;
 const currentJob=jobId?state.jobCache.get(jobId):null;
 if(requestedWorkspace==='rework'&&(!currentJob||String(currentJob.opportunity_id)!==String(id)))return;
 state.selected=id;markSelectedDeal();const panel=$('decisionPanel');panel.innerHTML=requestedWorkspace==='rework'?reworkDetail(d,currentJob):decisionContent(d);panel.classList.add('decision-selected');const nextBtn=panel.querySelector('#nextRework');if(nextBtn)nextBtn.onclick=nextRework;
 panel.querySelectorAll('[data-decision-tab]').forEach(b=>b.onclick=()=>{state.decisionTab=b.dataset.decisionTab;openDetail(id,true)});
 panel.querySelectorAll('[data-job]').forEach(b=>b.onclick=()=>performJob(b.dataset.job,b.dataset.action));
 const accountForm=$('accountForm');if(accountForm)accountForm.onsubmit=async e=>{e.preventDefault();if(state.jobBusy)return;const btn=accountForm.querySelector('button[type="submit"]');const feedback=$('accountFeedback');const job=selectedReworkJob();if(state.workspace==='rework'&&(!job||job.job_type!=='IDENTIFY_ACCOUNT'||String(job.opportunity_id)!==String(id))){feedback.textContent='Selecione um job válido no Aside.';return;}state.jobBusy=true;btn.disabled=true;try{const body=Object.fromEntries(new FormData(e.target));const result=await api('/api/opportunities/'+encodeURIComponent(id)+'/account',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!result.quality_gate?.eligible)throw Error('Quality Gate ainda não aprovado.');if(state.workspace==='rework'){const checked=await api('/api/opportunities/'+encodeURIComponent(id));const verified=checked.jobs.find(x=>String(x.id)===String(job.id));if(!verified||verified.status!=='VERIFIED')throw Error('Conta salva, mas a verificação do Job não foi confirmada. Consulte o histórico.');state.reworkConfirmation={jobId:String(job.id),opportunityId:String(id)};state.jobCache.set(String(job.id),{...job,status:'VERIFIED'});await openDetail(id,true);await refresh();}else{await refresh();await openDetail(id,true);}toast('Job verificado; Deal liberado ao Pipeline.','success');}catch(err){feedback.textContent=err.message;btn.disabled=false;}finally{state.jobBusy=false;}};
 const nba=panel.querySelector('#executeNBA');if(nba)nba.onclick=()=>openSalesAction(id);const history=panel.querySelector('#salesHistoryBtn');if(history)history.onclick=()=>openSalesAction(id,'history');
 const qual=$('qualForm');if(qual)qual.onsubmit=async e=>{e.preventDefault();try{await api('/api/opportunities/'+encodeURIComponent(id)+'/qualification',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});toast('Qualificação salva e regras de verificação reavaliadas.');await refresh();await openDetail(id,true)}catch(err){$('qualFeedback').textContent=err.message}};
 const act=$('actForm');if(act)act.onsubmit=async e=>{e.preventDefault();try{await api('/api/opportunities/'+encodeURIComponent(id)+'/activities',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});toast('Atividade registrada no histórico.');await refresh();await openDetail(id,true)}catch(err){$('actFeedback').textContent=err.message}};
 // Keep viewport position stable when changing Rework selection.
 }catch(e){toast('Falha ao abrir oportunidade: '+e.message,'error')}}
Object.keys(filterIds).forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>scheduleRefresh()));
$('prev').onclick=()=>{if(state.page>1){state.page--;state.dealOrder=[];state.selected=null;refresh()}};$('next').onclick=()=>{if(state.page<state.pages){state.page++;state.dealOrder=[];state.selected=null;refresh()}};
// Scoring policy button is bound dynamically when the XAI panel is rendered.
$('policyBtn').onclick=()=>{$('policyOverlay').classList.remove('hidden')};
$('policyClose').onclick=$('policyShade').onclick=()=>{$('policyOverlay').classList.add('hidden')};
// RC4: defer protected API requests until demo persona/session initialization.

function toast(message,kind='success'){
 const el=$('jobToast');el.textContent=message;el.className='job-toast '+kind;
 el.setAttribute('role','status');
}
function jobCategory(j){return j.job_type==='IDENTIFY_ACCOUNT'?'data':'commercial';}
function jobCard(j){const selected=String(j.id)===String(state.selectedReworkJob);return `<article class="job-card rework-job-card job-status-${esc(j.status)} ${selected?'selected':''}" data-job-card="${j.id}" tabindex="0" role="button" aria-pressed="${selected}" aria-label="Selecionar job ${j.id}, oportunidade ${esc(j.opportunity_id)}"><div class="job-card-top"><span class="job-identity">JOB #${j.id} · DEAL ${esc(j.opportunity_id)}</span><span class="job-state">${esc(j.status.replaceAll('_',' '))}</span></div><div class="job-card-title"><span class="job-priority">${esc(j.priority)}</span><b>${esc(actionNames[j.job_type]||j.job_type)}</b></div><p>${esc(j.account||'Conta não identificada')} · ${esc(j.sales_agent)}</p><div class="job-card-meta">Deal Score: <strong>${Number(j.deal_score).toFixed(1)}</strong></div></article>`;}

function visibleReworkJobs(){return state.jobOrder.map(id=>state.jobCache.get(id)).filter(Boolean).filter(j=>state.jobCategory==='all'||jobCategory(j)===state.jobCategory).sort((a,b)=>Number(a.status==='RESOLVED')-Number(b.status==='RESOLVED'));}
function renderJobBoard(){
 const jobs=visibleReworkJobs();
 const pages=Math.max(1,Math.ceil(jobs.length/state.reworkPageSize));state.reworkPage=Math.max(1,Math.min(state.reworkPage,pages));
 const visible=jobs.slice((state.reworkPage-1)*state.reworkPageSize,state.reworkPage*state.reworkPageSize);
 $('jobsBoard').innerHTML=visible.length?visible.map(jobCard).join(''):'<p class="empty-jobs">Nenhum job nesta categoria. Escolha outro filtro ou atualize a fila.</p>';
 $('jobsBoard').querySelectorAll('[data-job-card]').forEach(card=>{card.tabIndex=0;card.setAttribute('role','button');card.onclick=e=>{const jobId=card.dataset.jobCard;const job=state.jobCache.get(jobId);if(!job)return;if(state.selectedReworkJob===jobId && state.selected===String(job.opportunity_id))return;state.reworkConfirmation=null;state.selectedReworkJob=jobId;state.workspaceRequest++;state.decisionTab='execution';state.detailRequest++;renderJobBoard();openDetail(String(job.opportunity_id),false,jobId);};card.onkeydown=e=>{if((e.key==='Enter'||e.key===' ')&&!e.target.closest('button')){e.preventDefault();card.click();}};});
 // Rework job cards are selection-only; correction is performed in Main.
 const counts={commercial:0,data:0,all:state.jobCache.size};
 state.jobCache.forEach(j=>counts[jobCategory(j)]++);
 $('jobCount').textContent=`${jobs.length} jobs · página ${state.reworkPage} de ${pages}`;
 const nav=$('reworkPagination');if(nav){nav.hidden=jobs.length===0;$('reworkPageInfo').textContent=`Página ${state.reworkPage} de ${pages}`;$('reworkPrev').disabled=state.reworkPage<=1;$('reworkNext').disabled=state.reworkPage>=pages;}
}
async function refreshJobs(){
 try {
  const agent=$('agent').value;
  const qs=new URLSearchParams({limit:'500',history:state.jobHistory?'1':'0'});
  if(agent)qs.set('sales_agent',agent);
  const d=await api('/api/jobs?'+qs);
  $('historyToggle').textContent=state.jobHistory?'Ver ativos':'Ver histórico';
  state.jobCache=new Map(d.jobs.map(j=>[String(j.id),j]));
  const incoming=d.jobs.map(j=>String(j.id));
  const kept=state.jobOrder.filter(id=>state.jobCache.has(id));
  state.jobOrder=state.selected?[...kept,...incoming.filter(id=>!kept.includes(id))]:incoming;
  renderJobBoard();
  if(rc4Persona?.role==='SELLER'&&rc4Persona.seller){$('sellerReworkCount').textContent=num(d.jobs.filter(j=>j.status!=='RESOLVED').length);}
  if(state.workspace==='rework' && !state.reworkConfirmation && (!state.selectedReworkJob || !state.jobCache.has(state.selectedReworkJob))) { if(!state.selectedReworkJob || !state.jobCache.has(state.selectedReworkJob)) selectWorkspaceFirst('rework'); }
 }catch(e){$('jobsBoard').textContent='Falha ao carregar jobs: '+e.message;}
}
function jobButtons(j){return j.status==='OPEN'||j.status==='REOPENED'?`<button class="outline" data-job="${j.id}" data-action="START">Iniciar</button>`:j.status==='IN_PROGRESS'?`<button class="outline" data-job="${j.id}" data-action="RESOLVE">Marcar resolvido</button>`:j.status==='RESOLVED'?'<small>Verificação pendente · veja a orientação acima</small>':'';}
async function performJob(id,action){
 if(state.jobBusy)return;
 const key=String(id),job=state.jobCache.get(key);
 const card=$('jobsBoard').querySelector(`[data-job-card="${key}"]`);
 state.jobBusy=true;
 if(card){card.classList.add('job-working');card.querySelectorAll('button').forEach(b=>b.disabled=true);}
 try{
  const result=await api('/api/jobs/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});
  if(job){job.status=result.status;state.jobCache.set(key,job);}
  // Update in place: do not rerank or replace the full queue after a transition.
  if(card&&job){const replacement=document.createElement('div');replacement.innerHTML=jobCard(job);card.replaceWith(replacement.firstElementChild);
    const current=$('jobsBoard').querySelector(`[data-job-card="${key}"]`);
    current.classList.add('job-updated');current.querySelectorAll('[data-job]').forEach(b=>b.onclick=()=>performJob(b.dataset.job,b.dataset.action));
    current.onclick=e=>{if(e.target.closest('[data-job]'))return;state.selectedReworkJob=key;state.decisionTab='execution';openDetail(job.opportunity_id);};
  }
  toast(`Job #${id} · ${job?.opportunity_id||''}: ${result.status}. Posição preservada.`, 'success');
  await refresh();
  if(state.selected)await openDetail(state.selected,true);
 }catch(e){toast('Não foi possível atualizar o job: '+e.message,'error');if(card)card.querySelectorAll('button').forEach(b=>b.disabled=false);}
 finally{state.jobBusy=false;}
}
$('historyToggle').onclick=()=>{state.reworkConfirmation=null;state.jobHistory=!state.jobHistory;refreshJobs();toast(state.jobHistory?'Exibindo histórico completo.':'Exibindo fila ativa.');};

$('jobCategory').onchange=e=>{state.reworkConfirmation=null;state.jobCategory=e.target.value;state.reworkPage=1;renderJobBoard();toast('Filtro aplicado; posições dos demais jobs preservadas.');};

// V4.0 shell navigation and theme; does not mutate CRM/Closed-Loop state.
const themeToggle=$('themeToggle');
function applyTheme(theme){document.body.classList.toggle('theme-light',theme==='light');themeToggle.textContent=theme==='light'?'☾ Dark':'☀ Light';themeToggle.setAttribute('aria-pressed',String(theme==='light'));}
let currentTheme='dark';try{currentTheme=localStorage.getItem('g4_cockpit_theme')||'dark';}catch(_e){}applyTheme(currentTheme);
themeToggle.addEventListener('click',()=>{currentTheme=document.body.classList.contains('theme-light')?'dark':'light';applyTheme(currentTheme);try{localStorage.setItem('g4_cockpit_theme',currentTheme);}catch(_e){}});
$('reworkPrev').onclick=()=>{state.reworkPage=Math.max(1,state.reworkPage-1);renderJobBoard();selectWorkspaceFirst('rework');};
$('reworkNext').onclick=()=>{state.reworkPage++;renderJobBoard();selectWorkspaceFirst('rework');};
async function selectWorkspaceFirst(workspace){
 const request=++state.workspaceRequest;
 const first=workspace==='rework'?visibleReworkJobs().slice((state.reworkPage-1)*state.reworkPageSize)[0]:null;
 const id=workspace==='rework'?first?.opportunity_id:state.dealOrder[0];
 if(!id){$('decisionPanel').innerHTML=`<div class="decision-empty"><h2>${workspace==='rework'?'Nenhuma pendência':'Nenhuma oportunidade'}</h2><p>Não há itens disponíveis nesta fila.</p></div>`;return;}
 if(workspace==='rework'){state.selectedReworkJob=String(first.id);renderJobBoard();}
 if(request===state.workspaceRequest && workspace===state.workspace){state.decisionTab=workspaceToDecisionTab(workspace);await openDetail(String(id),false,workspace==='rework'?String(first.id):null);}
}
// V4.4-A: UI-only workspace separation; existing API, jobs, scoring and history remain unchanged.
function workspaceToDecisionTab(workspace){return {pipeline:'overview',qualification:'qualification',rework:'execution',history:'history'}[workspace]||'overview';}
function setWorkspace(workspace){
 if(!['pipeline','qualification','rework','history'].includes(workspace))return;
 if(workspace!=='pipeline'&&salesModalDeal)closeSalesAction();
 state.reworkConfirmation=null;state.workspace=workspace;state.decisionTab=workspaceToDecisionTab(workspace);state.selected=null;state.detailRequest++;if(workspace!=='rework')$('decisionPanel').innerHTML='<div class="decision-empty"><h2>Carregando oportunidade...</h2></div>';
 document.body.dataset.workspace=workspace;
 document.querySelectorAll('[data-workspace]').forEach(b=>{const active=b.dataset.workspace===workspace;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));});
 const help={pipeline:'Pipeline · selecione um Deal para entender a prioridade e a próxima ação.',qualification:'Qualificação · informações comerciais do Deal selecionado; não é Data Rework.',rework:'Data Rework · corrija defeitos bloqueantes; o Deal ingressa no Pipeline após validação.',history:'Histórico · consulte atividades e eventos do Deal selecionado.'};
 if($('workspaceHelp'))$('workspaceHelp').textContent=help[workspace];
 $('asideDeals').hidden=workspace==='rework';$('asideRework').hidden=workspace!=='rework';
 // V4.4-B: the Aside is the sole deal queue; no duplicate main list.
 if(workspace==='rework'){if(visibleReworkJobs().length)selectWorkspaceFirst(workspace);else refreshJobs().then(()=>selectWorkspaceFirst(workspace));}
 else if(state.dealOrder.length)selectWorkspaceFirst(workspace);
 else $('decisionPanel').innerHTML=`<div class="decision-empty"><h2>${{pipeline:'Pipeline',qualification:'Qualificação',rework:'Data Rework',history:'Histórico'}[workspace]}</h2><p>Selecione uma oportunidade ${workspace==='rework'?'na lista de pendências à direita':'na lista de Deals à direita'} para continuar.</p></div>`;
}
document.querySelectorAll('[data-workspace]').forEach(b=>b.onclick=()=>setWorkspace(b.dataset.workspace));
setWorkspace('pipeline');

// V4.1: read-only hierarchy; workspace selection synchronizes existing dashboard filters.
const hierarchyState={data:null,region:null,manager:null,seller:null};
function initials(name){return String(name||'RO').trim().split(/\s+/).slice(0,2).map(w=>w[0]).join('').toUpperCase();}
// Public-submission privacy and IP policy: initials only; no photographs or image lookups.
function avatarMarkup(name){return esc(initials(name));}
function setAvatarElement(id,name){const node=$(id);if(!node)return;node.textContent=initials(name);}
function setHierarchyContext(name,role){$('workspaceName').textContent=name;$('workspaceRole').textContent=role;setAvatarElement('navAvatar',name);setAvatarElement('headerAvatar',name);$('headerAvatar').title=role+' · '+name;$('navAvatar').title=role+' · '+name;}
function hierarchyCard(label,sub,meta,level,value){return `<button type="button" class="hierarchy-card" data-level="${esc(level)}" data-value="${esc(value)}"><span class="hierarchy-avatar">${avatarMarkup(label)}</span><span class="hierarchy-card-body"><strong>${esc(label)}</strong><small>${esc(sub)}</small><em>${esc(meta)}</em></span><span class="hierarchy-chevron">›</span></button>`;}
function hierarchyRender(){
 const h=hierarchyState, region=h.data?.regions.find(r=>r.name===h.region), manager=region?.managers.find(m=>m.name===h.manager), seller=manager?.sellers.find(v=>v.name===h.seller);
 const trail=['RevOps',h.region,h.manager,h.seller].filter(Boolean);$('hierarchyTrail').textContent=trail.join('  ›  ');
 $('hierarchyBack').hidden=trail.length<=1;
 $('hierarchyTitle').textContent=trail.join(' · ');
 let cards=[], subtitle='', sectors='';
 if(!region){subtitle='Selecione uma região para explorar seus gestores, vendedores e setores.';cards=h.data.regions.map(r=>hierarchyCard(r.name,'Região comercial',`${r.total} ativos · ${r.engaging} Engaging · ${r.prospecting} Prospecting`,'region',r.name));}
 else if(!manager){subtitle='Selecione um gerente. Setores exibidos abaixo representam oportunidades abertas, não Won/Lost.';cards=region.managers.map(m=>hierarchyCard(m.name,'Gerente regional',`${m.total} deals · ${m.sellers.length} vendedores`,'manager',m.name));sectors='<div class="hierarchy-sector-title">Setores da região · oportunidades ativas</div><div class="hierarchy-sector-list">'+region.sectors.map(v=>`<span class="hierarchy-sector">${esc(v.name)} <b>${v.total}</b></span>`).join('')+'</div>';}
 else if(!seller){subtitle='Selecione um vendedor para filtrar sua carteira no pipeline.';cards=manager.sellers.map(v=>hierarchyCard(v.name,'Vendedor',`${v.total} deals · ${v.engaging} Engaging · ${v.prospecting} Prospecting`,'seller',v.name));}
 else {subtitle=`Carteira de ${seller.name}: ${seller.total} oportunidades ativas. Utilize os cards de deal na fila ou o pipeline abaixo.`;cards=[`<div class="hierarchy-summary"><strong>${seller.total}</strong><span>Oportunidades ativas</span></div>`,`<div class="hierarchy-summary"><strong>${seller.engaging}</strong><span>Engaging</span></div>`,`<div class="hierarchy-summary"><strong>${seller.prospecting}</strong><span>Prospecting</span></div>`];}
 $('hierarchySubtitle').textContent=subtitle;$('hierarchyCards').innerHTML=cards.join('');$('hierarchySectors').innerHTML=sectors;
 $('hierarchyCards').querySelectorAll('[data-level]').forEach(b=>b.onclick=()=>hierarchySelect(b.dataset.level,b.dataset.value));
 setHierarchyContext(seller?.name||manager?.name||region?.name||'RevOps',seller?'Seller workspace':manager?'Manager workspace':region?'Regional workspace':'Executive overview');
}
function hierarchySyncFilters(){
 const h=hierarchyState;
 $('region').value=h.region||'';$('manager').value=h.manager||'';$('agent').value=h.seller||'';
 state.page=1;state.dealOrder=[];state.selected=null;refresh();
}
async function hierarchySelect(level,value){
 const h=hierarchyState;
 if(rc4Persona && ((rc4Persona.role==='MANAGER'&&level==='manager')||(rc4Persona.role==='SELLER'&&level==='seller'))){
  const field=rc4Persona.role==='MANAGER'?'manager':'seller';
  try{const result=await api('/api/demo/identity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({[field]:value})});
   rc4Persona=result.persona;rc4Landing(rc4Persona);state.selected=null;state.dealOrder=[];
  }catch(e){toast('Identidade não selecionada: '+e.message,'error');return;}
 }

 if(level==='region'){h.region=value;h.manager=null;h.seller=null;}
 if(level==='manager'){h.manager=value;h.seller=null;}
 if(level==='seller')h.seller=value;
 hierarchyRender();sellerNavSync();if(rc4Persona?.role==='HEAD'||rc4Persona?.manager||rc4Persona?.seller)hierarchySyncFilters();
}
$('hierarchyBack').onclick=()=>{const h=hierarchyState;if(h.seller)h.seller=null;else if(h.manager)h.manager=null;else h.region=null;hierarchyRender();hierarchySyncFilters();};
$('hierarchyHome').onclick=()=>{hierarchyState.region=null;hierarchyState.manager=null;hierarchyState.seller=null;hierarchyRender();hierarchySyncFilters();};
async function loadHierarchy(){try{hierarchyState.data=await api('/api/hierarchy');hierarchyRender();if(rc4Persona?.role==='HEAD')headRenderManagers();}catch(e){$('hierarchyCards').textContent='Não foi possível carregar hierarquia: '+e.message;}}

// Low-frequency synchronization for a local workspace; never refresh an actively edited form.
setInterval(()=>{if(document.visibilityState==='visible'&&!state.jobBusy&&!document.querySelector('#qualForm:focus-within, #accountForm:focus-within, #actForm:focus-within'))refresh();},30000);

$('trendClose').onclick=closeTrend;

// Align fixed overlay with the Main viewport while avoiding page reflow.
function positionTrendOverlay(){const main=document.querySelector('.shell-main');if(!main)return;const rect=main.getBoundingClientRect();const left=Math.max(8,rect.left+12);const width=Math.max(240,Math.min(window.innerWidth-left-8,rect.width-24));document.documentElement.style.setProperty('--trend-left',left+'px');document.documentElement.style.setProperty('--trend-width',width+'px');}
window.addEventListener('resize',positionTrendOverlay,{passive:true});
window.addEventListener('scroll',positionTrendOverlay,{passive:true});
positionTrendOverlay();

// V4.6-A: context-locked commercial action center. No external CRM updates.
let salesModalDeal=null, salesModalTab='qualification', salesModalData=null, salesModalRequest=0, salesModalMode='execute';
function closeSalesAction(){salesModalRequest++;$('salesActionOverlay').hidden=true;salesModalDeal=null;salesModalData=null;}
function salesTabForNBA(r){return r.next_best_action==='REVIEW_ENGAGEMENT'?'activity':'qualification';}
async function openSalesAction(id,tab=null){
 if(state.workspace!=='pipeline'||state.selected!==id)return;
 const request=++salesModalRequest;
 salesModalDeal=id;salesModalMode=tab==='history'?'history':'execute';salesModalTab=salesModalMode==='history'?'history':(tab||'qualification');
 $('salesActionTabs').hidden=salesModalMode==='history';
 $('salesModalTitle').textContent=salesModalMode==='history'?'Histórico de Atividades':'Sales Action Center';
 document.querySelector('.sales-modal-header small').textContent=salesModalMode==='history'?'PIPELINE · CONSULTA E RASTREABILIDADE':'PIPELINE · EXECUÇÃO COMERCIAL';
 $('salesActionOverlay').hidden=false;
 $('salesDealLabel').textContent='Deal '+id;$('salesModalContent').innerHTML='<p>Carregando dados comerciais...</p>';
 try{const data=await api('/api/sales-action/'+encodeURIComponent(id));if(request!==salesModalRequest||state.selected!==id||state.workspace!=='pipeline')return;
 salesModalData=data;if(!tab){const detail=await api('/api/opportunities/'+encodeURIComponent(id));if(request!==salesModalRequest)return;salesModalTab=salesTabForNBA(detail.opportunity);}
 renderSalesAction();$('salesActionOverlay').querySelector('.sales-modal').focus();
 }catch(e){if(request===salesModalRequest)$('salesModalContent').textContent='Não foi possível abrir o Action Center: '+e.message;}}
async function reloadSalesAction(){const id=salesModalDeal,tab=salesModalTab;if(!id)return;const data=await api('/api/sales-action/'+encodeURIComponent(id));if(id!==salesModalDeal)return;salesModalData=data;salesModalTab=tab;renderSalesAction();await refresh();if(state.selected===id&&state.workspace==='pipeline')await openDetail(id,true);}
function renderSalesAction(){if(!salesModalData)return;const d=salesModalData;
 document.querySelectorAll('[data-sales-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.salesTab===salesModalTab);b.setAttribute('aria-selected',String(b.dataset.salesTab===salesModalTab));});
 let body='';
 if(salesModalTab==='qualification'){const q=d.qualification||{};body=`<form id="salesQualForm"><h3>Qualificação comercial</h3><label>Decisor identificado ${choice('decision_maker',q.decision_maker||'unknown')}</label><label>Prazo de compra ${choice('timeline',q.timeline||'unknown')}</label><label>Orçamento ${choice('budget',q.budget||'unknown')}</label><label>Evidências<textarea name="notes" maxlength="1000" rows="3">${esc(q.notes||'')}</textarea></label><button class="primary" type="submit">Salvar qualificação</button></form>`;}
 else if(salesModalTab==='activity')body=`<form id="salesActivityForm"><h3>Registrar atividade</h3><label>Tipo<select name="action"><option value="CONTACT">Contato</option><option value="QUALIFY">Qualificação</option><option value="REVIEW">Revisão</option><option value="FOLLOW_UP">Follow-up</option><option value="OTHER">Outra</option></select></label><label>Resultado / evidência<textarea name="note" maxlength="1000" rows="4" required></textarea></label><button class="primary" type="submit">Registrar atividade</button></form>`;
 else if(salesModalTab==='plan')body=`<form id="salesPlanForm"><h3>Planejar próxima ação</h3><label>Ação<input name="title" maxlength="180" required></label><label>Responsável<input name="owner" maxlength="120" required></label><label>Prazo<input type="date" name="due_date" required></label><label>Prioridade<select name="priority"><option value="HIGH">Alta</option><option value="MEDIUM" selected>Média</option><option value="LOW">Baixa</option></select></label><button class="primary" type="submit">Criar plano de ação</button></form><h3>Planos registrados</h3>${d.plans.length?d.plans.map(p=>`<div class="sales-plan-row"><strong>${esc(p.title)}</strong><small>${esc(p.owner)} · ${esc(p.due_date)} · ${esc(p.priority)}</small><label>Status <select data-plan-status="${p.id}" ${['DONE','CANCELLED'].includes(p.status)?'disabled':''}>${[['OPEN','Aberto'],['IN_PROGRESS','Em andamento'],['DONE','Concluído'],['CANCELLED','Cancelado']].map(([v,t])=>`<option value="${v}" ${p.status===v?'selected':''}>${t}</option>`).join('')}</select></label></div>`).join(''):'<p>Nenhum plano registrado.</p>'}`;
 else if(salesModalTab==='closure')body=`<form id="salesClosureForm"><h3>Encerrar oportunidade</h3><p>Fechamento comercial definitivo; não confundir com atividade concluída.</p><div class="closure-commercial-summary"><div><small>Produto</small><strong>${esc(d.product||'Não informado')}</strong></div><div><small>Preço de catálogo (referência)</small><strong>${Number.isFinite(Number(d.catalog_price))&&d.catalog_price!==null?Number(d.catalog_price).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}):'Não disponível'}</strong></div><p>Quantidade não informada na origem. Preço de catálogo não é valor negociado nem receita realizada; moeda não especificada na origem.</p></div><label>Resultado<select name="outcome" id="closureOutcome"><option value="Won">Won — Negócio ganho</option><option value="Lost">Lost — Negócio perdido</option></select></label><div id="closureFields"><label>Valor efetivamente fechado<input type="text" name="close_value" inputmode="decimal" placeholder="Ex.: 1.234,56" autocomplete="off" required></label></div><label>Evidência comercial<textarea name="evidence" maxlength="1000" required></textarea></label><button class="primary" type="submit">Confirmar encerramento</button></form>`;
 else body=`<h3>Histórico comercial · ${esc(d.opportunity_id)}</h3>${[...d.activities.map(a=>({when:a.created_at,type:'ATIVIDADE · '+a.action,detail:a.note})),...d.events.map(e=>({when:e.created_at,type:e.event_type,detail:e.detail}))].sort((a,b)=>b.when.localeCompare(a.when)).slice(0,100).map(e=>`<div class="sales-timeline-item"><strong>${esc(e.type)}</strong><small>${esc(e.when)}</small><p>${esc(e.detail||'')}</p></div>`).join('')||'<p>Nenhuma atividade registrada.</p>'}`;
 $('salesModalContent').innerHTML='<p class="sales-form-feedback" id="salesFormFeedback" role="alert" aria-live="assertive" style="display:none;white-space:pre-wrap;border:1px solid #e8590c;border-radius:8px;padding:12px;margin:8px 0 16px;background:rgba(232,89,12,.10);font-weight:600"></p>'+body;
 const closureForm=$('salesClosureForm');if(closureForm){const outcome=$('closureOutcome');outcome.onchange=()=>{$('closureFields').innerHTML=outcome.value==='Won'?'<label>Valor efetivamente fechado<input type="text" name="close_value" inputmode="decimal" placeholder="Ex.: 1.234,56" autocomplete="off" required></label>':'<label>Motivo da perda<select name="loss_reason"><option value="PRICE">Preço</option><option value="COMPETITOR">Concorrência</option><option value="TIMING">Timing</option><option value="NO_FIT">Sem aderência</option><option value="OTHER">Outro</option></select></label>';};closureForm.onsubmit=async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(closureForm));if(payload.outcome==='Won'){const raw=String(payload.close_value||'').trim().replace(/\s/g,'');let normalized=raw;if(raw.includes(',')){normalized=raw.replace(/\./g,'').replace(',','.');}if(!/^(?:\d+)(?:\.\d{1,2})?$/.test(normalized)||!(Number(normalized)>0)){const fb=$('salesFormFeedback');fb.textContent='Informe um valor positivo válido, como 1234,56 ou 1.234,56 (até duas casas decimais).';fb.style.display='block';fb.scrollIntoView({behavior:'smooth',block:'nearest'});return;}payload.close_value=normalized;}if(!confirm('Confirmar encerramento definitivo da oportunidade?'))return;const id=salesModalDeal;const submit=closureForm.querySelector('button[type=submit]');const feedback=$('salesFormFeedback');submit.disabled=true;submit.textContent='Processando encerramento...';feedback.style.display='none';feedback.textContent='';try{await api('/api/opportunities/'+encodeURIComponent(id)+'/close',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});feedback.textContent='✓ Oportunidade encerrada com sucesso como '+payload.outcome+'. Atualizando as filas...';feedback.style.display='block';feedback.style.borderColor='#2f9e44';feedback.style.background='rgba(47,158,68,.14)';feedback.scrollIntoView({behavior:'smooth',block:'nearest'});closeSalesAction();state.selected=null;toast('Oportunidade encerrada com sucesso como '+payload.outcome+'.');try{await refresh();}catch(refreshError){toast('Encerramento salvo; atualize a página para sincronizar as filas.','error');}}catch(err){feedback.textContent='Encerramento NÃO realizado: '+err.message+'\nO valor informado foi preservado. Corrija a pendência e tente novamente.';feedback.style.display='block';feedback.style.borderColor='#e03131';feedback.style.background='rgba(224,49,49,.12)';feedback.scrollIntoView({behavior:'smooth',block:'nearest'});}finally{submit.disabled=false;submit.textContent='Confirmar encerramento';}};}
 for(const [formId,endpoint] of [['salesQualForm','qualification'],['salesActivityForm','activities'],['salesPlanForm','sales-plan']]){const form=$(formId);if(form)form.onsubmit=async e=>{e.preventDefault();const id=salesModalDeal;const button=form.querySelector('button[type="submit"]');button.disabled=true;try{await api('/api/opportunities/'+encodeURIComponent(id)+'/'+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(form)))});await reloadSalesAction();const fb=$('salesFormFeedback');if(fb){fb.textContent=endpoint==='qualification'?'✓ Qualificação salva com sucesso. Pendências comerciais reavaliadas e verificadas quando os requisitos foram atendidos.':'✓ Alterações salvas com sucesso no SQLite.';fb.style.display='block';fb.style.borderColor='#2f9e44';fb.style.background='rgba(47,158,68,.14)';fb.style.color='var(--foreground,#fff)';fb.scrollIntoView({behavior:'smooth',block:'nearest'});}}catch(err){const fb=$('salesFormFeedback');if(fb){fb.textContent='Não foi possível salvar: '+err.message;fb.style.display='block';fb.style.borderColor='#e03131';fb.style.background='rgba(224,49,49,.12)';}button.disabled=false;}};}
 $('salesModalContent').querySelectorAll('[data-plan-status]').forEach(el=>el.onchange=async()=>{try{await api('/api/opportunities/'+encodeURIComponent(salesModalDeal)+'/sales-plan-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:el.dataset.planStatus,status:el.value})});await reloadSalesAction();}catch(err){$('salesFormFeedback').textContent=err.message;}});
}
document.querySelectorAll('[data-sales-close]').forEach(b=>b.addEventListener('click',closeSalesAction));
document.querySelectorAll('[data-sales-tab]').forEach(b=>b.addEventListener('click',()=>{if(salesModalMode!=='execute')return;salesModalTab=b.dataset.salesTab;renderSalesAction();}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('salesActionOverlay').hidden)closeSalesAction();});

// RC4: one-click demo personas. Server owns authorization; this cover is navigation only.
// RC4 Navigation Fix: persona transition invalidates previous hierarchy, filters and selection.
let personaEpoch=0;
function resetPersonaNavigation(){
 personaEpoch++;hierarchyState.data=null;hierarchyState.region=null;hierarchyState.manager=null;hierarchyState.seller=null;
 for(const id of Object.keys(filterIds)){const el=$(id);if(el)el.value='';}
 state.page=1;state.selected=null;state.selectedReworkJob=null;state.dealOrder=[];state.dealRows.clear();state.jobCache.clear();state.jobOrder=[];
 state.detailRequest++;state.workspaceRequest++;state.reworkConfirmation=null;state.jobHistory=false;
 if(state.filterTimer)clearTimeout(state.filterTimer);
 closeTrend();closeSalesAction();
 $('hierarchyCards').innerHTML='';$('hierarchyTrail').textContent='';$('decisionPanel').innerHTML='<div class="decision-empty"><h2>Selecione um contexto</h2></div>';
}
// RC4 Seller: selector lives in Navbar, independent of the analytical hierarchy panel.
function sellerRenderSelectors(){
 const h=hierarchyState, region=h.data?.regions?.find(r=>r.name===h.region),manager=region?.managers?.find(m=>m.name===h.manager);
 const regionEl=$('sellerRegionButtons'), managerEl=$('sellerManagerButtons'), sellerEl=$('sellerSellerButtons');
 if(!regionEl)return;
 regionEl.innerHTML=(h.data?.regions||[]).map(r=>`<button type="button" class="head-region-button ${h.region===r.name?'active':''}" data-seller-region="${esc(r.name)}">${esc(r.name)}</button>`).join('');
 managerEl.innerHTML=region?region.managers.map(m=>`<button type="button" class="head-manager-button ${h.manager===m.name?'active':''}" data-seller-manager="${esc(m.name)}"><strong>${esc(m.name)}</strong></button>`).join(''):'<p class="head-data-note">Selecione uma região.</p>';
 sellerEl.innerHTML=manager?manager.sellers.map(v=>`<button type="button" class="head-manager-button ${h.seller===v.name?'active':''}" data-seller-person="${esc(v.name)}"><strong>${esc(v.name)}</strong><small>${num(v.total)} oportunidades ativas</small></button>`).join(''):'<p class="head-data-note">Selecione um manager.</p>';
 regionEl.querySelectorAll('button').forEach(b=>b.onclick=()=>sellerSelectContext('region',b.dataset.sellerRegion));
 managerEl.querySelectorAll('button').forEach(b=>b.onclick=()=>sellerSelectContext('manager',b.dataset.sellerManager));
 sellerEl.querySelectorAll('button').forEach(b=>b.onclick=()=>sellerSelectContext('seller',b.dataset.sellerPerson));
}
async function sellerSelectContext(level,value){
 const h=hierarchyState;
 if(level!=='seller' && rc4Persona?.seller){
  try{const reset=await api('/api/demo/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona:'seller'})});rc4Persona=reset.persona;}
  catch(e){toast('Não foi possível limpar a identidade anterior: '+e.message,'error');return;}
 }
 if(level==='region'){h.region=value;h.manager=null;h.seller=null;}
 if(level==='manager'){h.manager=value;h.seller=null;}
 if(level==='seller'){
  try{const r=await api('/api/demo/identity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seller:value})});rc4Persona=r.persona;h.seller=value;}
  catch(e){toast('Não foi possível selecionar vendedor: '+e.message,'error');return;}
 }
 state.selected=null;state.selectedReworkJob=null;state.dealOrder=[];state.dealRows.clear();state.jobCache.clear();state.jobOrder=[];
 state.detailRequest++;state.workspaceRequest++;
 $('region').value=h.region||'';$('manager').value=h.manager||'';$('agent').value=h.seller||'';
 document.body.classList.toggle('seller-ready',!!h.seller);
 sellerRenderSelectors();sellerNavSync();
 if(h.seller){setWorkspace('pipeline');await refresh();}
 else {renderAsideDeals();$('jobsBoard').innerHTML='';$('totalLabel').textContent='';$('decisionPanel').innerHTML='<div class="decision-empty"><h2>Selecione um vendedor</h2><p>Escolha região, manager e vendedor no Navbar para visualizar o Opportunity 360 e Next Best Action.</p></div>';}
}
// Seller-specific navigation: reuse existing persistent Pipeline/Rework APIs.
function sellerNavSync(){
 const nav=$('sellerExecutionNav');if(!nav)return;
 const active=rc4Persona?.role==='SELLER'&&!!rc4Persona.seller;
 nav.hidden=rc4Persona?.role!=='SELLER';
 nav.querySelectorAll('[data-seller-queue]').forEach(b=>{b.disabled=!active;b.classList.toggle('active',active&&state.workspace===b.dataset.sellerQueue);});
 if(!active){$('sellerPipelineCount').textContent='—';$('sellerReworkCount').textContent='—';}
 sellerRenderSelectors();
}
document.querySelectorAll('[data-seller-queue]').forEach(b=>b.addEventListener('click',()=>{
 if(rc4Persona?.role!=='SELLER'||!rc4Persona.seller)return;
 setWorkspace(b.dataset.sellerQueue);sellerNavSync();
}));
function rc4Landing(persona){
 const role=persona.role;document.body.dataset.persona=role.toLowerCase();document.body.classList.toggle('manager-ready',role==='MANAGER'&&!!persona.manager);document.body.classList.toggle('seller-ready',role==='SELLER'&&!!persona.seller);
 const heading=$('rc4LandingHeading'),detail=$('rc4LandingDetail');
 if(role==='HEAD'){heading.textContent='Executive Command Center';detail.textContent='Visão estratégica corporativa: indicadores, conversão, tendências e exposição comercial. Explore o drill-down quando necessário.';}
 else if(role==='MANAGER'){heading.textContent=persona.manager?'Management Performance · '+persona.manager:'Management Performance · Regiões';detail.textContent=persona.manager?'Equipe selecionada. Acompanhe a carteira e reatribua oportunidades autorizadas.':'Selecione Central, East ou West e depois o gerente para ativar o workspace tático.';}
 else {heading.textContent=persona.seller?'Seller Execution Center · '+persona.seller:'Seller Selection';detail.textContent=persona.seller?'Selecione Pipeline, Rework ou Histórico no Navbar e trabalhe sua fila no Aside. Opportunity 360 disponível no Main.':'Selecione uma região, um gerente e então o vendedor demonstrativo.';}
 $('managementCenter').hidden=role!=='MANAGER';$('managerNav').hidden=role!=='MANAGER';$('managerSellerAside').hidden=true;
 if(role==='MANAGER'){managerReset();managerInit();managerLoad();}
 sellerNavSync();
 $('headExecutive').hidden=role!=='HEAD';$('headRegionNav').hidden=role!=='HEAD';$('headManagerAside').hidden=role!=='HEAD';
 if(role==='HEAD'){headReset();headRenderRegions();headRenderManagers();headLoad();}
}
async function activateDemoPersona(persona){
 resetPersonaNavigation();rc4Persona=persona;$('personaLabel').textContent=persona.label;
 $('demoCover').hidden=true;rc4SetPersona(persona);rc4Landing(persona);
 const epoch=personaEpoch;await loadHierarchy();if(epoch!==personaEpoch)return; if(persona.role==='SELLER'){sellerRenderSelectors();sellerNavSync();}
 if(persona.role!=='HEAD'&&(persona.manager||persona.seller))await refresh();
}
async function chooseDemoPersona(key){
 try{const result=await api('/api/demo/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({persona:key})});await activateDemoPersona(result.persona);}
 catch(e){alert('Não foi possível selecionar a persona: '+e.message);}
}
document.querySelectorAll('[data-demo-persona]').forEach(b=>b.onclick=()=>chooseDemoPersona(b.dataset.demoPersona));
$('switchPersona').onclick=()=>{$('demoCover').hidden=false;};
(async()=>{try{const s=await api('/api/demo/session');if(!s.demo_mode){$('demoCover').hidden=true;await refresh();await loadHierarchy();return;}if(s.persona)await activateDemoPersona(s.persona);}catch(e){}})();

let rc4Persona=null;
function rc4SetPersona(persona){rc4Persona=persona;}

// RC4 Head workspace: independent executive selection, no operational drill-down inheritance.
const headState={region:'Central',manager:'',sector:'All Sectors',request:0};
function headReset(){headState.region='Central';headState.manager='';headState.sector='All Sectors';headState.request++;}
function headRenderRegions(){
 $('headRegionButtons').innerHTML=['Central','East','West'].map(r=>`<button type="button" class="head-region-button ${headState.region===r?'active':''}" data-head-region="${r}">${r}</button>`).join('');
 $('headRegionButtons').querySelectorAll('button').forEach(b=>b.onclick=()=>{headState.region=b.dataset.headRegion;headState.manager='';headState.sector='All Sectors';headRenderRegions();headRenderManagers();headLoad();});
}
function headRenderManagers(){
 const r=hierarchyState.data?.regions?.find(x=>x.name===headState.region);
 $('headManagerHint').textContent=headState.region+' · selecione um manager para refinar a análise';
 $('headManagerButtons').innerHTML=(r?.managers||[]).map(m=>`<button type="button" class="head-manager-button ${headState.manager===m.name?'active':''}" data-head-manager="${esc(m.name)}"><strong>${esc(m.name)}</strong><small>${num(m.total)} oportunidades ativas</small></button>`).join('')+(headState.manager?'<button class="head-manager-clear" type="button">Todos os managers</button>':'');
 $('headManagerButtons').querySelectorAll('[data-head-manager]').forEach(b=>b.onclick=()=>{headState.manager=b.dataset.headManager;headState.sector='All Sectors';headRenderManagers();headLoad();});
 const clear=$('headManagerButtons').querySelector('.head-manager-clear');if(clear)clear.onclick=()=>{headState.manager='';headState.sector='All Sectors';headRenderManagers();headLoad();};
}
function headMetric(label,value,detail=''){return `<div class="head-metric"><span>${esc(label)}</span><strong>${esc(value)}</strong>${detail?`<small>${esc(detail)}</small>`:''}</div>`;}
function headCurrency(v){return v==null?'N/D':Number(v).toLocaleString('pt-BR',{maximumFractionDigits:2,minimumFractionDigits:2});}
async function headLoad(){
 if(document.body.dataset.persona!=='head')return;
 const request=++headState.request;
 const q=new URLSearchParams({region:headState.region,sector:headState.sector});if(headState.manager)q.set('manager',headState.manager);
 try{
 const d=await api('/api/executive/intelligence?'+q);if(request!==headState.request||document.body.dataset.persona!=='head')return;
 $('headScope').textContent=[headState.region,headState.manager||'Todos os managers',headState.sector].join(' · ');
 $('headSectorCards').innerHTML=d.sectors.map(s=>`<button class="head-sector-card ${s.name===headState.sector?'active':''}" type="button" data-head-sector="${esc(s.name)}"><strong>${esc(s.name)}</strong><span>${num(s.deals)} deals</span></button>`).join('');
 $('headSectorCards').querySelectorAll('button').forEach(b=>b.onclick=()=>{headState.sector=b.dataset.headSector;headLoad();});
 const a=d.account360,k=d.derived,t=d.stages,den=t.Won+t.Lost,pct=den?100*t.Won/den:0;
 $('headAnalytics').innerHTML=`<section class="panel head-analytic-panel"><h3>Deal Stage · Distribuição comercial</h3><div class="head-stage-row"><div class="head-donut" style="--won-percent:${pct}%"><div><b>${num(t.Won)}</b><small>Won</small><b>${num(t.Lost)}</b><small>Lost</small></div></div>${headMetric('Prospecting',num(t.Prospecting)+' deals')}${headMetric('Engaging',num(t.Engaging)+' deals')}</div></section>
 <section class="panel head-analytic-panel"><h3>1. Account 360° — Diagnóstico comercial</h3><p class="head-data-note">Escopo: ${esc(d.scope.region)} · ${esc(d.scope.manager)} · ${esc(d.scope.sector)}. Histórico de oportunidades; receita somente de Won.</p><div class="head-metric-grid">${headMetric('Total de deals',num(a.deals))}${headMetric('Contas identificadas',num(a.accounts))}${headMetric('Won',num(a.won))}${headMetric('Lost',num(a.lost))}${headMetric('Oportunidades abertas',num(a.open))}${headMetric('Receita Won (unidade da fonte)',headCurrency(a.won_revenue))}${headMetric('Ticket médio Won',a.avg_won_deal==null?'N/D':headCurrency(a.avg_won_deal))}${headMetric('Ciclo médio Won',a.avg_won_cycle_days==null?'N/D':num(a.avg_won_cycle_days)+' dias')}</div><h4>Principais contas por volume de deals</h4><div class="head-account-list">${a.top_accounts.map(x=>`<span>${esc(x.account)} <b>${num(x.deals)}</b></span>`).join('')}</div></section>
 <section class="panel head-analytic-panel"><h3>2. Indicadores comerciais derivados</h3><div class="head-metric-grid">${headMetric('Win Rate',k.win_rate==null?'N/D':num(k.win_rate)+'%','Won / (Won + Lost)')}${headMetric('Loss Rate',k.loss_rate==null?'N/D':num(k.loss_rate)+'%')}${headMetric('Deals encerrados',num(k.closed))}${headMetric('Deals abertos',num(k.open))}${headMetric('Exposição Lost (catálogo)',headCurrency(k.catalog_lost_exposure),'Referência comercial, não receita recuperável')}</div><h4>Conversão por coorte de entrada</h4><div class="head-cohort-chart">${k.cohorts.map(x=>`<div class="head-cohort-row"><span>${esc(x.month)}</span><div class="head-cohort-track"><i style="width:${x.win_rate??0}%"></i></div><strong>${x.win_rate==null?'N/D':num(x.win_rate)+'%'}</strong><small>${num(x.won)} W / ${num(x.lost)} L</small></div>`).join('')}</div><p class="head-data-note">Coortes por engage_date. Comparações não demonstram causalidade; a maturação das coortes pode variar.</p></section>`;
 }catch(e){if(request===headState.request)$('headAnalytics').textContent='Não foi possível carregar indicadores executivos: '+e.message;}
}

// RC4 Manager: tactical analysis is separate from Head and Seller workspaces.
const managerState={region:'Central',manager:'',seller:'',sector:'All Sectors',request:0};
function managerReset(){managerState.region='Central';managerState.manager='';managerState.seller='';managerState.sector='All Sectors';managerState.request++;document.body.classList.remove('manager-seller-selected');const nav=$('managerSellerNav');if(nav)nav.innerHTML='<p class="head-data-note">Selecione um manager.</p>';}
function managerInit(){
 const nav=$('managerRegionButtons');nav.innerHTML=['Central','East','West'].map(r=>`<button type="button" class="head-region-button ${managerState.region===r?'active':''}" data-manager-region="${r}">${r}</button>`).join('');
 nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{managerState.region=b.dataset.managerRegion;managerState.manager='';managerState.seller='';managerState.sector='All Sectors';document.body.classList.remove('manager-seller-selected');managerInit();managerLoad();});
}
async function managerChoose(name){
 try{
  const r=await api('/api/demo/identity',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({manager:name})});
  rc4Persona=r.persona;managerState.manager=name;managerState.seller='';managerState.sector='All Sectors';document.body.classList.remove('manager-seller-selected');
  document.body.classList.add('manager-ready');
  $('manager').value=name;$('region').value=managerState.region;$('agent').value='';
  managerLoad();await refresh();
 }catch(e){$('managerAnalytics').textContent='Não foi possível selecionar manager: '+e.message;}
}
function managerMetric(title,value,detail=''){return `<div class="head-metric"><small>${esc(title)}</small><strong>${esc(String(value))}</strong>${detail?`<span>${esc(detail)}</span>`:''}</div>`;}
$('managerSectorFilter').addEventListener('change',e=>{managerState.sector=e.target.value;managerState.seller='';managerLoad();});
async function managerLoad(){
 if(rc4Persona?.role!=='MANAGER')return;
 const req=++managerState.request;
 try{
  const q=new URLSearchParams({region:managerState.region,sector:managerState.sector});if(managerState.manager)q.set('manager',managerState.manager);
  const d=await api('/api/management/intelligence?'+q);if(req!==managerState.request||rc4Persona?.role!=='MANAGER')return;
  $('managerScope').textContent=managerState.region+' · '+(managerState.manager||'Selecione um manager')+' · '+managerState.sector;
  $('managerSectorFilter').innerHTML=d.sectors.map(x=>`<option value="${esc(x.name)}" ${x.name===managerState.sector?'selected':''}>${esc(x.name)} · ${num(x.deals)} deals</option>`).join('');
  $('managerSectorFilter').disabled=!managerState.manager;
  $('managerPicker').innerHTML=d.managers.map(m=>`<button type="button" class="head-region-button ${managerState.manager===m.name?'active':''}" data-choose-manager="${esc(m.name)}">${esc(m.name)} · ${num(m.deals)} deals</button>`).join('');
  $('managerPicker').querySelectorAll('button').forEach(b=>b.onclick=()=>managerChoose(b.dataset.chooseManager));
  const regions=d.regions.map(r=>`<button type="button" class="manager-comparison-card ${managerState.region===r.name?'active':''}" data-manager-region-card="${r.name}"><strong>${r.name}</strong><span>${num(r.deals)} deals</span><small>Win Rate ${r.win_rate??'N/D'}% · ${num(r.prospecting+r.engaging)} abertos</small></button>`).join('');
  let html=`<section class="panel head-analytic-panel"><h3>Comparativo regional · histórico</h3><div class="manager-region-grid">${regions}</div></section>`;
  if(managerState.manager){
   const t=d.team;
   html+=`<section class="panel head-analytic-panel"><h3>Equipe · ${esc(managerState.manager)}</h3><div class="head-metric-grid">${managerMetric('Deals históricos',num(t.deals))}${managerMetric('Win Rate',t.win_rate==null?'N/D':t.win_rate+'%','Won / negócios encerrados')}${managerMetric('Won',num(t.won))}${managerMetric('Lost',num(t.lost))}${managerMetric('Prospecting',num(t.prospecting))}${managerMetric('Engaging',num(t.engaging))}${managerMetric('Pipeline operacional',num(d.live_team_pipeline),'População atual')}</div></section>`;
   if(managerState.seller){
    const v=d.sellers.find(x=>x.name===managerState.seller);
    if(v)html+=`<section class="panel head-analytic-panel"><h3>Seller Performance · ${esc(v.name)}</h3><p class="head-data-note">Indicadores táticos do vendedor selecionado · ${esc(managerState.region)} / ${esc(managerState.manager)}</p><div class="head-metric-grid">${managerMetric('Deals históricos',num(v.deals))}${managerMetric('Win Rate',v.win_rate==null?'N/D':v.win_rate+'%','Won / negócios encerrados')}${managerMetric('Pipeline operacional',num(v.active_pipeline))}${managerMetric('Prioridade alta',num(v.high_priority))}</div><p class="head-data-note">Analise o desempenho antes de redistribuir oportunidades. O Opportunity 360 é exclusivo do workspace Vendedor.</p></section>`;
   }else html+='<section class="panel head-analytic-panel"><h3>Diagnóstico por vendedor</h3><p>Selecione um vendedor no Navbar para visualizar suas métricas e identificar necessidades de intervenção.</p></section>';
  }else html+='<section class="panel head-analytic-panel"><h3>Próximo passo</h3><p>Selecione um manager no Navbar para identificar os vendedores que precisam de intervenção.</p></section>';
  $('managerAnalytics').innerHTML=html;
  $('managerAnalytics').querySelectorAll('[data-manager-region-card]').forEach(b=>b.onclick=()=>{managerState.region=b.dataset.managerRegionCard;managerState.manager='';managerState.seller='';managerState.sector='All Sectors';document.body.classList.remove('manager-seller-selected');managerInit();managerLoad();});
  $('managerSellerNav').innerHTML=managerState.manager?d.sellers.map(v=>`<button type="button" class="head-manager-button ${managerState.seller===v.name?'active':''}" data-nav-seller="${esc(v.name)}"><strong>${esc(v.name)}</strong><small>${v.win_rate??'N/D'}% Win · ${num(v.active_pipeline)} ativos</small></button>`).join(''):'<p class="head-data-note">Selecione um manager.</p>';
  $('managerSellerNav').querySelectorAll('button').forEach(b=>b.onclick=()=>managerSelectSeller(b.dataset.navSeller));
 }catch(e){if(req===managerState.request)$('managerAnalytics').textContent='Não foi possível carregar gestão: '+e.message;}
}
async function managerSelectSeller(name){
 managerState.seller=name;
 // Selection is analytical only; Opportunity 360 and operational queues belong to Seller.
 $('agent').value=name;$('manager').value=managerState.manager;$('region').value=managerState.region;
 managerLoad();
}
