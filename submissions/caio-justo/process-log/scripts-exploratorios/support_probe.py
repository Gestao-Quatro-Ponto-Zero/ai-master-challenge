import sys,glob,re,time,pandas as pd,numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,f1_score,roc_auc_score
base=sys.argv[1]; pd.set_option('display.width',200); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',260)
d1=pd.read_csv(glob.glob(base+'/d1/*.csv')[0]); d2=pd.read_csv(glob.glob(base+'/d2/*.csv')[0])
print('D1',d1.shape); print(d1.isna().sum()); print(d1['Ticket Status'].value_counts())
print(d1[['Ticket Subject','Ticket Description','Resolution']].dropna().head(4))
td=d1['Ticket Description'].astype(str)
print('placeholder share',td.str.contains(r'\{[a-z_]+\}').mean(),'unique desc',td.nunique(), 'unique res',d1['Resolution'].nunique())
print('type x subject chi: subject per type'); print(pd.crosstab(d1['Ticket Subject'],d1['Ticket Type']).head(6))
cs=d1.dropna(subset=['Customer Satisfaction Rating']).copy(); print('CSAT',cs['Customer Satisfaction Rating'].value_counts(normalize=True).sort_index().round(3).to_dict())
for c in ['Ticket Priority','Ticket Channel','Ticket Type','Product Purchased']:
    print(c,cs.groupby(c)['Customer Satisfaction Rating'].mean().round(2).sort_values().iloc[[0,-1]].to_dict())
cs['fr']=pd.to_datetime(cs['First Response Time'],errors='coerce'); cs['tr']=pd.to_datetime(cs['Time to Resolution'],errors='coerce')
cs['ttr_h']=(cs.tr-cs.fr).dt.total_seconds()/3600; print('ttr h',cs.ttr_h.describe().round(1).to_dict(),'negative share',(cs.ttr_h<0).mean()); print('corr csat~ttr',cs[['ttr_h','Customer Satisfaction Rating']].corr().iloc[0,1])
print('dates',cs.fr.min(),cs.fr.max(),'purchase',d1['Date of Purchase'].min(),d1['Date of Purchase'].max())
# Text → type / priority signal
for tgt in ['Ticket Type','Ticket Priority']:
    x=d1.dropna(subset=[tgt]); a,b=train_test_split(x,test_size=.25,random_state=0,stratify=x[tgt]); v=TfidfVectorizer(max_features=30000,ngram_range=(1,2),sublinear_tf=True)
    m=LogisticRegression(max_iter=1000).fit(v.fit_transform(a['Ticket Description'].astype(str)),a[tgt]); print('D1 text→',tgt,'acc',round(accuracy_score(b[tgt],m.predict(v.transform(b['Ticket Description'].astype(str)))),3),'chance',round(x[tgt].value_counts(normalize=True).max(),3))
print('\nD2',d2.shape,list(d2.columns)); print(d2.Topic_group.value_counts()); print(d2.Document.isna().sum(),'dupes',d2.Document.duplicated().mean()); print(d2.Document.str.split().str.len().describe().round(1).to_dict())
print(d2.groupby('Topic_group').Document.first().str[:200])
a,b=train_test_split(d2,test_size=.2,random_state=0,stratify=d2.Topic_group); v=TfidfVectorizer(max_features=100000,ngram_range=(1,2),sublinear_tf=True); t=time.time(); xa=v.fit_transform(a.Document); m=LogisticRegression(max_iter=1000,C=5).fit(xa,a.Topic_group); print('train s',round(time.time()-t,1))
t=time.time(); pr=m.predict_proba(v.transform(b.Document)); print('ms/ticket',round((time.time()-t)*1000/len(b),3)); pred=m.classes_[pr.argmax(1)]; conf=pr.max(1)
print('D2 tfidf acc',round(accuracy_score(b.Topic_group,pred),3),'macroF1',round(f1_score(b.Topic_group,pred,average='macro'),3))
for th in [.5,.7,.8,.9,.95]:
    k=conf>=th; print('conf>=',th,'coverage',round(k.mean(),3),'acc',round((pred[k]==b.Topic_group[k]).mean(),3))
