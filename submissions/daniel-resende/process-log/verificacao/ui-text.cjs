// Executes the submitted text-building functions with a tiny DOM, without layout.
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor(tag, text='') { this.tag=tag; this.children=[]; this.value=text; this.attrs={}; this.nodeType=tag==='#text'?3:1; this.style={setProperty(){}}; this.classList={toggle(){},add(){},remove(){}}; }
  setAttribute(k,v){this.attrs[k]=String(v);if(k==='id')this.id=String(v);}
  addEventListener(){}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  get textContent(){return this.value+this.children.map(n=>n.textContent??String(n)).join(' ');}
  get visibleText(){return 'hidden' in this.attrs || this.hidden ? '' : this.value+this.children.map(n=>n.visibleText??String(n)).join(' ');}
  set textContent(v){this.value=v;this.children=[];}
}
const root='submissions/daniel-resende/solution';
const out='.verif/runtime/'+root+'/out/';
const doc={createElement:t=>new Element(t),createElementNS:(_,t)=>new Element(t),createTextNode:t=>new Element('#text',String(t))};
const fixture={console,document:doc,location:{search:'',hash:''},URLSearchParams,Intl,requestAnimationFrame(){},ResizeObserver:class{observe(){}}};
vm.createContext(fixture);
let code=fs.readFileSync(root+'/web/app.js','utf8');
if(!code.includes('  start();'))throw Error('Unexpected entry point');
code=code.replace('  start();',`globalThis.v={dealTip,renderSeller,renderManager,drawLine,fillHow,init:(i,t,s)=>{index=i;texts=t;current=s;},select:(name)=>{state.seller=name;}};`);
vm.runInContext(code,fixture);
const index=JSON.parse(fs.readFileSync(out+'index.json'));
const ai=JSON.parse(fs.readFileSync(root+'/ai/textos.json'));
const texts={meta:ai.meta,byId:new Map(ai.texts.map(t=>[t.id,t]))};
const v=fixture.v;
let score=JSON.parse(fs.readFileSync(out+'score-2018-01-01.json'));
v.init(index,texts,score);
for(const name of ['Kary Hendrixson','Anna Snelling','Carl Lin']){
 v.select(name);
 console.log('\nSELLER',name);
 console.log(v.renderSeller(score,false).map(n=>n.visibleText).join('\n'));
}
const svg=new Element('svg');
svg.parentNode={getBoundingClientRect:()=>({width:1000})};
v.drawLine(svg,score,score.sellers.find(s=>s.seller==='Boris Faz'),false);
console.log('\nBORIS_TIMELINE_LABELS',svg.visibleText);
const truncated=score.sellers.flatMap(s=>s.alive.filter(d=>d.days_left<138-d.days_open));
console.log('QUARTER_TRUNCATES_MAX_AGE',truncated.length,'of115');
console.log('BORIS_NGTVHTFH',JSON.stringify(score.sellers.find(s=>s.seller==='Boris Faz').alive.find(d=>d.id==='NGTVHTFH')));
score=JSON.parse(fs.readFileSync(out+'score-2017-10-02.json'));
v.init(index,texts,score);
console.log('\nHISTORICAL_AI_OVERLAP',JSON.stringify(score.sellers.flatMap(s=>s.alive.filter(d=>texts.byId.has('deal:'+d.id)).map(d=>({seller:s.seller,id:d.id,past_age:d.days_open,ai_age:texts.byId.get('deal:'+d.id).facts.days_open,past_play:d.play,ai_play:texts.byId.get('deal:'+d.id).facts.play_label})))));
const seller=score.sellers.find(s=>s.seller==='Cassey Cress');
const deal=seller.alive.find(d=>d.id==='GWOOPZE8');
console.log('\nPAST_TOOLTIP_WITH_AI GWOOPZE8');
console.log(v.dealTip(deal,score.meta.time_table).filter(Boolean).map(n=>n.textContent).join('\n'));
v.init(index,null,score);
console.log('\nPAST_TOOLTIP_WITHOUT_AI GWOOPZE8');
console.log(v.dealTip(deal,score.meta.time_table).filter(Boolean).map(n=>n.textContent).join('\n'));
