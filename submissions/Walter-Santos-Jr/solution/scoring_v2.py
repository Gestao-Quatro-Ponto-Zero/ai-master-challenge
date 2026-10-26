"""G4 Lead Scorer V2: reproducible, deterministic decision-support heuristic.
Run: python scoring_v2.py --dataset /path/to/archive.zip --output /path/to/output
No trained probability or claim of causal lift.
"""
import argparse, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

POLICY_VERSION='2.0-experimental'
WEIGHTS={'stage':0.40,'product':0.35,'account':0.25}

def read_data(path):
    with zipfile.ZipFile(path) as z:
        return {k:pd.read_csv(z.open(k+'.csv')) for k in ['sales_pipeline','products','accounts','sales_teams']}

def score(df, products, accounts, teams, weights=WEIGHTS):
    d=df.copy()
    d['product_normalized']=d['product'].replace({'GTXPro':'GTX Pro'})
    d=d.merge(products.rename(columns={'product':'product_normalized'}),on='product_normalized',how='left',validate='many_to_one')
    d=d.merge(accounts,on='account',how='left',validate='many_to_one')
    d=d.merge(teams,on='sales_agent',how='left',validate='many_to_one')
    assert d['sales_price'].notna().all() and d['manager'].notna().all()
    d=d[d.deal_stage.isin(['Engaging','Prospecting'])].copy()
    # Stage score is a decision-policy convention, not an empirical close probability.
    d['stage_component']=d['deal_stage'].map({'Prospecting':35.,'Engaging':75.})
    # Reference catalog economics only, not forecast deal value.
    prices=np.log1p(products.sales_price.astype(float))
    d['product_component']=100*(np.log1p(d.sales_price)-prices.min())/(prices.max()-prices.min())
    # Account scale: equal-weight rank percentiles of revenue and headcount in known accounts.
    # Missing account is neutral (50), never zero. Known-account percentile is a business hypothesis.
    ac=accounts[['account','revenue','employees']].copy()
    ac['account_scale_component']=50*(ac['revenue'].rank(pct=True)+ac['employees'].rank(pct=True))
    d=d.merge(ac[['account','account_scale_component']],on='account',how='left',validate='many_to_one')
    d['account_known']=d['account'].notna()
    d['account_component']=d['account_scale_component'].fillna(50.)
    d['priority_score']=sum(d[k+'_component']*w for k,w in weights.items())
    d['priority_score']=d['priority_score'].round(1)
    d['priority_band']=pd.cut(d.priority_score,[-0.1,45,65,100],labels=['LOW','MEDIUM','HIGH'],include_lowest=True)
    d['data_confidence']=np.where(d.account_known,'ACCOUNT_KNOWN','ACCOUNT_MISSING')
    d['next_best_action']=np.select([~d.account_known,d.deal_stage.eq('Prospecting')],['IDENTIFY_ACCOUNT','QUALIFY_OPPORTUNITY'],default='REVIEW_ENGAGEMENT')
    d['priority_rank_in_stage']=d.groupby('deal_stage')['priority_score'].rank(ascending=False,method='dense').astype(int)
    d['explanation']=d.apply(lambda r: (f"Estágio {r.deal_stage} ({r.stage_component:.0f}/100); preço de catálogo {r.sales_price:.0f} ({r.product_component:.1f}/100); " + (f"porte da conta ({r.account_component:.1f}/100)" if r.account_known else 'porte da conta desconhecido (neutro 50/100)') + '. Índice heurístico, não probabilidade de fechamento.'),axis=1)
    return d

def stats(d):
    return {'policy_version':POLICY_VERSION,'weights':WEIGHTS,'n_open':len(d),'score':{'min':float(d.priority_score.min()),'median':float(d.priority_score.median()),'max':float(d.priority_score.max()),'distinct':int(d.priority_score.nunique())},'bands':d.priority_band.value_counts().to_dict(),'stage_bands':pd.crosstab(d.deal_stage,d.priority_band).to_dict(orient='index'),'product_bands':pd.crosstab(d.product_normalized,d.priority_band).to_dict(orient='index'),'actions':d.next_best_action.value_counts().to_dict(),'missing_account':int((~d.account_known).sum()),'stage':d.deal_stage.value_counts().to_dict(),'top_20pct':d.nlargest(int(np.ceil(len(d)*.2)),'priority_score').product_normalized.value_counts().to_dict()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',default='/mnt/data/archive.zip');p.add_argument('--output',default='/mnt/data/g4_scoring_v2');args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    raw=read_data(args.dataset)
    d=score(raw['sales_pipeline'],raw['products'],raw['accounts'],raw['sales_teams'])
    cols=['opportunity_id','sales_agent','manager','regional_office','deal_stage','product_normalized','sales_price','account','sector','revenue','employees','engage_date','priority_score','priority_band','priority_rank_in_stage','stage_component','product_component','account_component','data_confidence','next_best_action','explanation']
    d[cols].sort_values(['deal_stage','priority_score'],ascending=[True,False]).to_csv(out/'scored_opportunities_v2.csv',index=False)
    result=stats(d)
    # sensitivity on weights: conservative shifts of 10 percentage points, renormalized
    baseline=set(d.nlargest(int(np.ceil(len(d)*.2)),'priority_score').opportunity_id)
    sens={}
    for k in WEIGHTS:
        for delta in [-.10,.10]:
            w=dict(WEIGHTS);w[k]+=delta; total=sum(w.values());w={a:b/total for a,b in w.items()}
            tmp=score(raw['sales_pipeline'],raw['products'],raw['accounts'],raw['sales_teams'],w)
            top=set(tmp.nlargest(len(baseline),'priority_score').opportunity_id)
            sens[f'{k}_{delta:+.0%}']={'top20_overlap':round(len(baseline&top)/len(baseline),4),'high_count_at_fixed_65':int((tmp.priority_score>65).sum())}
    result['weight_sensitivity']=sens
    with open(out/'metrics_v2.json','w') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
