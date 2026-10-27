import fs from "fs";
const ds=JSON.parse(fs.readFileSync("data/generated/dataset.json","utf8"));
const D=ds.deals, C=D.filter(d=>d.stage==="Won"||d.stage==="Lost"), O=D.filter(d=>d.stage==="Engaging"||d.stage==="Prospecting");
const days=(a,b)=>(new Date(b)-new Date(a))/864e5;
const acc=Object.fromEntries(ds.accounts.map(a=>[a.name,a]));
function wr(key,label,min=0){const g={};for(const d of C){const k=key(d);if(k==null)continue;(g[k]??={w:0,n:0});g[k].n++;if(d.stage==="Won")g[k].w++;}
 const rows=Object.entries(g).filter(([,v])=>v.n>=min).map(([k,v])=>[k,v.n,(v.w/v.n*100).toFixed(1)]).sort((a,b)=>b[2]-a[2]);
 const r=rows.map(x=>+x[2]);console.log(`\n## ${label}  spread ${Math.min(...r)}–${Math.max(...r)}`);for(const x of rows)console.log("  ",x.join(" | "));}
wr(d=>d.product,"produto");wr(d=>d.sector,"setor");wr(d=>d.regionalOffice,"escritório");wr(d=>d.manager,"manager");wr(d=>d.agent,"vendedor");
wr(d=>{const a=acc[d.account];return a.employees<500?"<500":a.employees<2000?"500-2k":a.employees<5000?"2k-5k":"5k+"},"porte(func)");
wr(d=>{const a=acc[d.account];return a.subsidiaryOf?"subsidiária":"independente"},"subsidiária");
wr(d=>d.engageDate.slice(0,7),"mês de engage");
wr(d=>d.closeDate.slice(0,7),"mês de close");
const cyc=s=>C.filter(d=>d.stage===s).map(d=>days(d.engageDate,d.closeDate)).sort((a,b)=>a-b);
const q=(a,p)=>a[Math.floor((a.length-1)*p)];
for(const s of["Won","Lost"]){const a=cyc(s);console.log(`\n${s} ciclo: p10 ${q(a,.1)} p25 ${q(a,.25)} p50 ${q(a,.5)} p75 ${q(a,.75)} p90 ${q(a,.9)} max ${a.at(-1)}`);}
// win rate by cycle bucket
const b=[0,15,30,45,60,75,90,120,200];const g={};for(const d of C){const c=days(d.engageDate,d.closeDate);const k=b.findLast(x=>c>=x);(g[k]??={w:0,n:0});g[k].n++;if(d.stage==="Won")g[k].w++;}
console.log("\nwin rate por ciclo:");for(const k of b)if(g[k])console.log("  >=",k,g[k].n,(g[k].w/g[k].n*100).toFixed(1));
const ages=O.filter(d=>d.engageDate).map(d=>days(d.engageDate,ds.referenceDate)).sort((a,b)=>a-b);
console.log(`\nEngaging idade (dias até ${ds.referenceDate}): p10 ${q(ages,.1)} p50 ${q(ages,.5)} p90 ${q(ages,.9)} max ${ages.at(-1)}; >138: ${ages.filter(x=>x>138).length}`);
console.log("open por agente (min/max):",(()=>{const m={};for(const d of O)m[d.agent]=(m[d.agent]||0)+1;const v=Object.values(m);return[Math.min(...v),Math.max(...v),v.length]})());
// agent x product
const ap={};for(const d of C){const k=d.agent+"|"+d.product;(ap[k]??={w:0,n:0});ap[k].n++;if(d.stage==="Won")ap[k].w++;}
const apr=Object.values(ap).filter(v=>v.n>=30).map(v=>v.w/v.n*100);console.log("agente×produto (n>=30) spread",Math.min(...apr).toFixed(1),Math.max(...apr).toFixed(1),apr.length);
// won close_value vs list
console.log("\nopen por produto:",Object.entries(O.reduce((m,d)=>(m[d.product]=(m[d.product]||0)+1,m),{})));
