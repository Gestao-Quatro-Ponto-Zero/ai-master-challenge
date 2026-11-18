const vm=require('vm'),fs=require('fs');
const S=require("path").join(__dirname, "../../../solution/app/");
function mk(search=""){
  const store={};const els={};
  const el=(id)=>els[id]||(els[id]={id,innerHTML:"",hidden:false,open:false,value:"",classList:{toggle(){},remove(){},contains(){return false}},querySelector(){return {scrollTop:0}},addEventListener(){},close(){this.open=false},showModal(){this.open=true}});
  const ctx={console,URLSearchParams,setTimeout(){},clearTimeout(){},
    localStorage:{getItem:k=>k in store?store[k]:null,setItem:(k,v)=>{store[k]=String(v)}},
    document:{getElementById:el,body:{classList:{toggle(){},remove(){}},appendChild(){}},documentElement:{dataset:{},scrollWidth:0,clientWidth:0},querySelector(){return {innerHTML:"",dataset:{},classList:{toggle(){},remove(){}},setAttribute(){}}},querySelectorAll(){return []},addEventListener(){} ,createElement(){return{click(){},style:{},dataset:{}}}},
    location:{search},navigator:{},confirm:()=>true,Date,Math,JSON,Object,Number,String,Set,Array,URL,Blob:function(){}};
  ctx.window=ctx; ctx.window.scrollTo=()=>{}; ctx.addEventListener=()=>{}; ctx.print=()=>{};
  vm.createContext(ctx);
  for(const f of ["data.js","workflow.js","charts.js","app.js"]) vm.runInContext(fs.readFileSync(S+f,"utf8"),ctx,{filename:f});
  ctx.__store=store; ctx.__els=els;
  return ctx;
}
const run=(ctx,code)=>vm.runInContext(code,ctx);
const strip=h=>h.replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim();
module.exports={mk,run,strip};
if(require.main===module){
  const ctx=mk();
  for(const name of ["Kary Hendrixson","Cassey Cress","Darcel Schlecht","Hayden Neloms"]){
    run(ctx,`enter("vendedor",${JSON.stringify(name)})`);
    const r=run(ctx,`(()=>{const items=workItems();const q=Object.values(todayParts(items)).flat();
      const c=a=>q.filter(i=>actionOf(i)===a).length;
      return {total:q.length,ligar:c("ligar"),mensagem:c("mensagem"),retorno:c("retorno"),
       abordar:q.filter(i=>i.deal.lista==="abordar").length,reativar:q.filter(i=>i.deal.lista==="reativar").length,
       semConta:q.filter(i=>!i.deal.conta).length,
       parked:queueOf(items,"encerrar").length, carteira:items.length,
       first12:q.slice(0,12).map(i=>[i.deal.lista,i.deal.conta||"(sem conta)",i.deal.produto,i.deal.preco,i.deal.score,i.deal.faixa,i.deal.idade,i.deal.fechaEsteMes?"HOT":""].join("|")),
       focoAll:q.filter(i=>i.deal.lista==="foco").map(i=>[i.deal.preco,i.deal.score,i.deal.faixa,i.deal.idade].join("/")).join("  ")}})()`);
    console.log("\n==",name,JSON.stringify(r,null,1));
    console.log("NAV:",strip(ctx.__els.nav.innerHTML));
    const html=ctx.__els.view.innerHTML;
    console.log("rows rendered page1:",(html.match(/class="tr/g)||[]).length, "| pager:",strip((html.match(/<div class="pager">[\s\S]*?<\/span>/)||[""])[0]));
    console.log("aside:",strip((html.match(/<p class="aside">[\s\S]*?<\/p>/)||[""])[0]));
    console.log("tabs:",strip((html.match(/<div class="tabs">[\s\S]*?<\/div>/)||[""])[0]));
  }
  // popups
  run(ctx,`enter("vendedor","Kary Hendrixson")`);
  const ids=run(ctx,`(()=>{const q=Object.values(todayParts(workItems())).flat();return [q[0].deal.id,q.find(i=>i.deal.lista==="reativar").deal.id, q.find(i=>!i.deal.conta).deal.id]})()`);
  for(const id of ids){run(ctx,`state.openId=${JSON.stringify(id)};state.showDetails=true;render()`);console.log("\nPOPUP",id,":",strip(ctx.__els.sheet.innerHTML).slice(0,1800));}
}
