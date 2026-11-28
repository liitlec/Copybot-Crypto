from pathlib import Path
import numpy as np
import pandas as pd
rng=np.random.default_rng(2311)
data=pd.read_csv(Path(__file__).with_name('journal.csv'),parse_dates=['day'])
def ci(q,columns,fun):
    v=q[columns].groupby(q.day.dt.to_period('W')).sum().to_numpy()
    sample=v[rng.integers(len(v),size=(5000,len(v)))].sum(axis=1)
    return np.round(np.quantile(fun(sample),[.025,.975]),2)
for n,z in data[data.hour==9].groupby('period',sort=False):
    z=z.copy();s=z.signal_calme; y=z.label.eq('calme')
    z['correct']=s & y;z['calm']=y;z['one']=1
    # Contrôle calendaire, comparé aux mêmes proportions de jours de la semaine et de mois.
    group=z.day.dt.strftime('%Y-%m')+'-'+z.day.dt.weekday.astype(str)
    expected=y.groupby(group).transform('mean')[s].mean()
    print(n,'Calme',s.sum(),sum(y),sum(s&y),len(z),'precision/rappel',round(sum(y&s)/sum(s),3),round(sum(y&s)/sum(y),3),'IC_ecart_pp',ci(z,['correct','signal_calme','calm','one'],lambda a:100*(a[:,0]/a[:,1]-a[:,2]/a[:,3])),'base_calendrier',round(expected,3),'repartition',z[s].label.value_counts().to_dict())
    q=z[z.cassure=='acceptée'].copy()
    q['long']=q.net*10000-4;q['diff']=q.bp_cassure-q.long
    print('cassure',len(q),'achat',q.sens.eq(1).sum(),'rendement, long, diff',q[['bp_cassure','long','diff']].mean().round(2).to_dict(),'IC moyenne bp',ci(q,['bp_cassure','one'],lambda a:a[:,0]/a[:,1]),'IC diff vs achat',ci(q,['diff','one'],lambda a:a[:,0]/a[:,1]))
