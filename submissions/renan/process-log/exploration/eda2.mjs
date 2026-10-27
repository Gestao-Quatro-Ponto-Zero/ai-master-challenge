import fs from "fs";
const ds=JSON.parse(fs.readFileSync("data/generated/dataset.json","utf8"));
const C=ds.deals.filter(d=>d.stage==="Won"||d.stage==="Lost");
const days=(a,b)=>(new Date(b)-new Date(a))/864e5;
console.log("P(win | ainda aberto em t):");
for(const t of[0,7,14,30,45,60,75,90,105,120,130]){const s=C.filter(d=>days(d.engageDate,d.closeDate)>t);console.log("  t>",t,s.length,(s.filter(d=>d.stage==="Won").length/s.length*100).toFixed(1));}
// split-half reliability agent win rate: by close date halves
const half=d=>d.closeDate<"2017-08-01"?0:1;
const g={};for(const d of C){const k=d.agent;(g[k]??=[{w:0,n:0},{w:0,n:0}]);const h=g[k][half(d)];h.n++;if(d.stage==="Won")h.w++;}
const xs=[],ys=[];for(const v of Object.values(g)){if(v[0].n>30&&v[1].n>30){xs.push(v[0].w/v[0].n);ys.push(v[1].w/v[1].n);}}
const corr=(a,b)=>{const m=x=>x.reduce((s,y)=>s+y,0)/x.length;const ma=m(a),mb=m(b);let n=0,da=0,db=0;for(let i=0;i<a.length;i++){n+=(a[i]-ma)*(b[i]-mb);da+=(a[i]-ma)**2;db+=(b[i]-mb)**2;}return n/Math.sqrt(da*db)};
console.log("corr vendedor 1ª×2ª metade:",corr(xs,ys).toFixed(2),"n",xs.length);
const g2={};for(const d of C){const k=d.agent+"|"+d.product;(g2[k]??=[{w:0,n:0},{w:0,n:0}]);const h=g2[k][half(d)];h.n++;if(d.stage==="Won")h.w++;}
const a=[],b=[];for(const v of Object.values(g2)){if(v[0].n>=15&&v[1].n>=15){a.push(v[0].w/v[0].n);b.push(v[1].w/v[1].n);}}
console.log("corr vendedor×produto:",corr(a,b).toFixed(2),"n",a.length);
const g3={};for(const d of C){const k=d.product;(g3[k]??=[{w:0,n:0},{w:0,n:0}]);const h=g3[k][half(d)];h.n++;if(d.stage==="Won")h.w++;}
console.log("produto por metade",Object.entries(g3).map(([k,v])=>k+" "+(v[0].w/v[0].n*100).toFixed(0)+"/"+(v[1].w/v[1].n*100).toFixed(0)).join(", "));
// chi2-ish: agent spread vs binomial noise
const rates=Object.values(g).map(v=>{const w=v[0].w+v[1].w,n=v[0].n+v[1].n;return{p:w/n,n}});const P=.632;
const chi=rates.reduce((s,r)=>s+(r.p-P)**2*r.n/(P*(1-P)),0);console.log("chi2 vendedor",chi.toFixed(1),"df",rates.length-1);
// close value: won by product std of discount
// quarter-end check on Lost vs Won counts by close month
const m={};for(const d of C){const k=d.closeDate.slice(5,7);(m[k]??={W:0,L:0});m[k][d.stage==="Won"?"W":"L"]++;}console.log(m);
