import json
sh={'Hardware':.2847,'HR Support':.2282,'Access':.1489,'Miscellaneous':.1476,'Storage':.0581,'Purchase':.0515,'Internal Project':.0443,'Administrative rights':.0368}
S=['conservador','base','otimista']
P={ # variavel: (cons, base, ot)
'V':(3000,5000,8000),
'pe':(sh['Purchase']+sh['Storage'], sh['Purchase']+sh['Storage']+0.5*sh['Access'], sh['Purchase']+sh['Storage']+sh['Access']),
'ts':(0.36,0.50,0.65),
'aht':(8,12,18),
'tri':(0.5,1.0,1.5),
'tf':(2.0,1.5,1.0),
'r':(0.15,0.10,0.05),
'k':(0.5,0.5,0.5),
'ch':(round(3000*1.7/182,2),round(4109*1.8/182,2),round(4399*2.0/182,2)),
'real':(0.25,0.50,0.75),
'tool':(2000,1500,1000),
'mnt':(5000,3500,2500),
'impl':(120000,80000,50000),
}
def calc(p):
    E=p['V']*p['pe']; Sx=E*p['ts']; F=E-Sx
    Ha=(Sx*(1-p['r'])*p['aht']-Sx*p['r']*p['k']*p['aht'])/60
    Ht=p['V']*p['tri']/60; Hf=F*p['tf']/60; H=Ha+Ht-Hf
    VP=H*p['ch']; ER=VP*p['real']; C=p['tool']+p['mnt']; L=ER-C
    roi=L/C; pb=p['impl']/L if L>0 else None
    roi12=(12*L-p['impl'])/(p['impl']+12*C)
    return dict(E=E,S=Sx,F=F,Ha=Ha,Ht=Ht,Hf=Hf,H=H,FTE=H/146,VP=VP,ER=ER,C=C,L=L,roi=roi,roi_pot=(VP-C)/C,roi12=roi12,pb=pb)
R={s:calc({k:v[i] for k,v in P.items()}) for i,s in enumerate(S)}
base={k:v[1] for k,v in P.items()}
# break-even volume (base): ER=C
import math
def L_of(V): q=dict(base);q['V']=V;return calc(q)['L']
lo,hi=1,10**6
while hi-lo>1:
    m=(lo+hi)//2
    if L_of(m)>0: hi=m
    else: lo=m
R['breakeven_V_base']=hi
for real in (0.75,1.0):
    q=dict(base);q['real']=real;lo,hi=1,10**6
    while hi-lo>1:
        m=(lo+hi)//2;q['V']=m
        if calc(q)['L']>0: hi=m
        else: lo=m
    R[f'breakeven_V_real{int(real*100)}']=hi
names={'V':'Volume mensal','pe':'% elegível à automação','ts':'Taxa de sucesso da automação','aht':'Tempo médio por chamado','tri':'Tempo de triagem manual poupado','tf':'Fricção por tentativa falha','r':'% retrabalho por erro','ch':'Custo-hora do agente','real':'Taxa de realização financeira','tool':'Custo mensal ferramentas IA','mnt':'Custo manutenção mensal'}
sens=[]
for k,n in names.items():
    vals=[]
    for i in (0,2):
        q=dict(base);q[k]=P[k][i];vals.append(calc(q)['L'])
    sens.append(dict(var=n,cons=vals[0],ot=vals[1],amp=abs(vals[1]-vals[0])))
sens.sort(key=lambda x:-x['amp'])
R['sens']=sens; R['base_L']=calc(base)['L']; R['P']=P
json.dump(R,open('/home/ubuntu/g4_challenge/fase3/roi_results.json','w'),indent=1,default=str)
for s in S: print(s,{k:(round(v,2) if isinstance(v,float) else v) for k,v in R[s].items()})
print('BE',R['breakeven_V_base'],R['breakeven_V_real75'],R['breakeven_V_real100']); print(R['base_L'])
for x in sens: print(x)
