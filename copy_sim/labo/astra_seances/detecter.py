"""Rejouer localement : python detecter.py (numpy, pandas, scikit-learn)."""
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
BASE=Path(__file__).resolve().parent
def read(name):
    return pd.read_csv(BASE / (name+'.csv'),header=None,names=['date','o','h','l','c'],parse_dates=['date']).set_index('date')
def clean(x):
    return x.sort_index().loc[lambda z:~z.index.duplicated()]

def features(df,hour):
    records=[]
    for day,g in df.groupby(df.index.normalize()):
        g=g.copy();g.index=g.index.hour
        hours=[1,5,9,13,17]
        if not set(hours).issubset(g.index) or day.weekday()>4: continue
        g=g.loc[hours]
        pre=g.loc[:hour-4];post=g.loc[hour:]
        o=pre.o.iloc[0];c=pre.c.iloc[-1];h=pre.h.max();l=pre.l.min()
        start=post.o.iloc[0];end=post.c.iloc[-1];hi=post.h.max();lo=post.l.min()
        if h<=l or hi<=lo: continue
        gross=(post.c/post.o-1)*10000
        sign=np.sign(g.c-g.o).shift(1).loc[hour:]
        loc=(g.c-g.l)/(g.h-g.l).replace(0,np.nan)
        fade=pd.Series(np.select([loc>.75,loc<.25],[-1.,1.],0.),index=g.index).shift(1).loc[hour:]
        t=float((sign*gross-4*sign.abs()).sum());r=float((fade*gross-4*fade.abs()).sum())
        overlap=max(0,min(pre.h.iloc[-1],pre.h.iloc[-2])-max(pre.l.iloc[-1],pre.l.iloc[-2]))/(h-l)
        records.append(dict(day=day,pre=(h-l)/o,body=(c-o)/(h-l),location=(2*c-h-l)/(h-l),overlap=overlap,
            lastclose=c,hi=g.h.max(),lo=g.l.min(),daily=(g.h.max()-g.l.min())/o,
            post=(hi-lo)/start,bodypost=(end-start)/(hi-lo),exc=max(hi-start,start-lo)/start,
            net=(end-start)/start,t=t,r=r))
    d=pd.DataFrame(records).set_index('day')
    def med(col):return d[col].shift(1).rolling(20).median()
    d['morn']=np.log(d.pre/med('pre'))
    d['recent']=np.log(d.daily.shift(1).rolling(3).median()/med('daily'))
    prevhi=d.hi.shift(1);prevlo=d.lo.shift(1)
    d['prevloc']=((d.lastclose-prevlo)/(prevhi-prevlo)).clip(-2,3)
    d['eff']=d.body.abs()
    d['prempos']=d.location.abs()
    d['beyond']=np.maximum(0,np.maximum(d.prevloc-1,-d.prevloc))
    for j in range(4):d['dow'+str(j)]=(d.index.dayofweek==j).astype(float)
    typical=med('post')
    # L'oscillation cible un retour observable près du prix de décision après une excursion.
    d['label']=np.select([d.post<.70*typical,d.bodypost.abs()>=.65,(d.exc>=.40*typical)&(d.net.abs()<=.30*d.exc)],
                         ['calme','tendance','retour'],default='mixte')
    d['up']=(d.net>0).astype(int)
    return d.loc[typical.notna()].dropna()
def fit(x,y):
    return make_pipeline(StandardScaler(),LogisticRegression(C=.3,max_iter=1000)).fit(x,y)
periods=['2017–2021','2022–2023','2024–févr26','mars–sept26']
classes=['calme','retour','tendance']
features_market=['morn','recent','eff','prempos','overlap','beyond']
calendar=['dow0','dow1','dow2','dow3']
def run(h,hist,control):
    d=features(hist,h);e=features(control,h)
    tr=d.loc[:'2016'];print('APPRENTISSAGE',h,len(tr),tr.index.min(),tr.index.max())
    f=features_market+calendar
    model=fit(tr[f],tr.label);base=fit(tr[calendar],tr.label)
    direction=fit(tr[f+['body','location','prevloc']],tr.up)
    probs=pd.DataFrame(model.predict_proba(tr[f]),columns=model.classes_)
    thresholds=probs[classes].quantile(.80)
    d0=direction.predict_proba(tr[f+['body','location','prevloc']])[:,1];dcut=np.quantile(abs(d0-.5),.80)
    subsets=[d.loc['2017':'2021'],d.loc['2022':'2023'],d.loc['2024':],e]
    out=[]
    for period,data in zip(periods,subsets):
        z=data.copy();p=pd.DataFrame(model.predict_proba(z[f]),columns=model.classes_,index=z.index)
        pb=base.predict_proba(z[calendar]);select=p[classes].ge(thresholds)
        # Ex aequo entre signaux : plus grand rapport au seuil de validation.
        choice=(p[classes]/thresholds).idxmax(axis=1).where(select.any(axis=1),'inconnu')
        z['regle']=choice
        for cl in classes:z['signal_'+cl]=select[cl];z['prob_'+cl]=p[cl]
        z['pred']=p.idxmax(axis=1);z['calpred']=base.predict(z[calendar])
        z['direction']=direction.predict_proba(z[f+['body','location','prevloc']])[:,1]
        z['sensfort']=(z.direction-.5).abs()>=dcut
        z['direction_bp']=np.sign(z.direction-.5)*z.net*10000-4
        z['fixe']=(z.t+z.r)/2
        z['selection']=np.select([choice=='tendance',choice=='retour',choice=='calme'],[z.t,z.r,0],z.fixe)
        z['simple']= (z.morn<=np.log(.7)) & (z.recent<=0)
        z['period']=period;z['hour']=h
        z['cal_ll']=-np.log(pb[np.arange(len(z)),np.searchsorted(base.classes_,z.label)])
        z['mod_ll']=-np.log(p.to_numpy()[np.arange(len(z)),np.searchsorted(model.classes_,z.label)])
        out.append(z)
    return pd.concat(out)

if __name__=='__main__':
    hist=clean(pd.concat([read('ancien'),read('h4')]))
    h1=read('h1');h1.index=h1.index.tz_convert('UTC').tz_localize(None)
    group=h1.resample('4h',origin='start_day',offset='1h')
    ctrl=group.agg({'o':'first','h':'max','l':'min','c':'last'}).loc[group.size()==4]
    result=pd.concat([run(h,hist,ctrl) for h in [9,13]])
    result.to_csv(BASE/'decisions.csv')
