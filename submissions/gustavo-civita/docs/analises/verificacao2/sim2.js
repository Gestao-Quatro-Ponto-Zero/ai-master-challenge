const {mk,run,strip}=require('./sim.js');
let ctx=mk();
const kpis=()=>strip((ctx.__els.view.innerHTML.match(/<div class="summary">[\s\S]*?<\/div><\/div>|<div class="summary">[\s\S]*?<\/div>\s*<div class="panel">/)||[""])[0]).slice(0,200);
// --- manager
run(ctx,`enter("gerente","Toda a empresa")`);
console.log("EVERYONE KPIs:",kpis());
console.log(run(ctx,`(()=>{const it=workItems();return {total:it.length, enc:it.filter(i=>situacaoOf(i)==="encerrar").length, reat:it.filter(i=>situacaoOf(i)==="reativar").length, negl:it.filter(isNeglected).length}})()`));
console.log("panel:",strip(ctx.__els.view.innerHTML).match(/negociações abertas somam[^.]*\./)?.[0]);
// mark a foco deal as won + direct win without prior contact
const fid=run(ctx,`DATA.deals.find(d=>d.lista==="foco").id`);
run(ctx,`Workflow.add(DEAL_BY_ID[${JSON.stringify(fid)}],"ganhou");render()`);
console.log("after 1 foco WON -> KPIs:",kpis());
console.log("Resultados panel after direct win:",strip(ctx.__els.view.innerHTML).match(/Resultados dos contatos.{0,160}/)?.[0]);
// region hidden filter
run(ctx,`state.filtroRegiao="West";render();go("carteira")`);
console.log("Carteira after region=West chosen in Time: ",strip(ctx.__els.view.innerHTML).match(/\d+ a \d+ de [\d.]+ negociações/)?.[0]," has region select in carteira?",/filtro-regiao/.test(ctx.__els.view.innerHTML));
run(ctx,`state.filtroRegiao="";`);
// team manager with zero foco
run(ctx,`enter("gerente","Dustin Brinkmann")`);
console.log("Dustin KPIs:",kpis()); console.log("alert rows:",(ctx.__els.view.innerHTML.match(/class="alert"/g)||[]).length);
// --- seller without open deals
for (const n of ["Donn Cantrell","Carl Lin"]) { const c=mk("?vendedor="+encodeURIComponent(n)); console.log(n,"session:",run(c,"JSON.stringify(state.session)"), "listed on entry?", run(c,`state.entering="vendedor";pageEntrar().includes(${JSON.stringify(n)})`)); }
// --- workflow sequences
ctx=mk(); run(ctx,`enter("vendedor","Kary Hendrixson")`);
const st=(id)=>run(ctx,`(()=>{const d=DEAL_BY_ID[${JSON.stringify(id)}];const s=Workflow.statusOf(d,Workflow.byDeal()[d.id]);return [s.fase,s.modo,s.tentativas,s.tarefa].join(" | ")})()`);
const q=run(ctx,`Object.values(todayParts(workItems())).flat().map(i=>i.deal.id)`);
const foco=q[0], reat=run(ctx,`Object.values(todayParts(workItems())).flat().find(i=>i.deal.lista==="reativar").deal.id`);
const add=(id,t,x="{}")=>run(ctx,`Workflow.add(DEAL_BY_ID[${JSON.stringify(id)}],"${t}",${x})`);
add(foco,"nao_atendeu"); console.log("1x nao_atendeu:",st(foco));
run(ctx,"Workflow.advanceDay();Workflow.advanceDay()"); console.log("+2d:",st(foco));
add(foco,"nao_atendeu"); add(foco,"nao_atendeu"); console.log("3x:",st(foco));
run(ctx,`Workflow.undoLast(${JSON.stringify(foco)})`); console.log("undo:",st(foco));
add(reat,"enviou"); console.log("reat enviou:",st(reat));
run(ctx,"for(let i=0;i<3;i++)Workflow.advanceDay()"); console.log("+3d:",st(reat), "| verb:",run(ctx,`(()=>{const i=workItems().find(i=>i.deal.id===${JSON.stringify(reat)});return verbOf(i)+" / acao "+actionOf(i)})()`));
add(reat,"enviou");add(reat,"enviou"); console.log("3 msgs (not due):",st(reat));
run(ctx,"for(let i=0;i<3;i++)Workflow.advanceDay()"); console.log("3 msgs due:",st(reat));
// mixed: 2 msgs + respondeu + past-date return
const reat2=run(ctx,`Object.values(todayParts(workItems())).flat().filter(i=>i.deal.lista==="reativar"&&i.status.fase==="fila")[0].deal.id`);
add(reat2,"enviou");add(reat2,"respondeu"); console.log("enviou+respondeu:",st(reat2));
add(reat2,"retornar",`{retornoEm:"2020-01-01T12:00:00.000Z"}`); console.log("retorno no passado:",st(reat2));
add(reat2,"retornar",`{retornoEm:"lixo"}`); console.log("retorno data invalida:",st(reat2));
// counts on Hoje now + deal age unchanged after clock advance
run(ctx,"render()"); console.log("NAV:",strip(ctx.__els.nav.innerHTML)," dias avancados:",run(ctx,"Workflow.daysAhead()")," idade do deal foco (inalterada?):",run(ctx,`DEAL_BY_ID[${JSON.stringify(foco)}].idade`));
// empty filter
run(ctx,`state.busca="zzzzzz";render()`); console.log("filtro vazio:",strip(ctx.__els.view.innerHTML).match(/Nada para fazer[^<]*/)?.[0]);
run(ctx,`state.busca="";state.filtroProduto="GTK 500";render()`); console.log("produto sem linhas:",/class="empty"/.test(ctx.__els.view.innerHTML));
// corrupted localStorage
ctx.__store["leadscorer.eventos.v3"]="{bad"; try{run(ctx,"render()");console.log("log corrompido: ok")}catch(e){console.log("log corrompido QUEBRA:",e.message)}
ctx.__store["leadscorer.eventos.v3"]=JSON.stringify([{id:"NAOEXISTE",tipo:"enviou",quando:new Date().toISOString()}]); try{run(ctx,"render()");console.log("evento de deal inexistente: ok")}catch(e){console.log("QUEBRA:",e.message)}
// stale event: deal that left data.js (closed in CRM) but page open; and event tipo desconhecido
ctx.__store["leadscorer.eventos.v3"]=JSON.stringify([{id:foco,tipo:"xyz",quando:new Date().toISOString()}]); console.log("tipo desconhecido ->",st(foco));
// unused identifiers
const src=require('fs').readFileSync(require("path").join(__dirname, "../../../solution/app/app.js"),"utf8");
for(const n of ["contactLabel","CHIPS","TODAY_SIZE","filtro-acao","isToday","LISTS\\[","\\.nome\\b"]) console.log(n,(src.match(new RegExp(n,"g"))||[]).length);
