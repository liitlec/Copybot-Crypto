"""Exemple : python score_matin.py h4.csv 2025-03-19
Entrée CSV sans entête : date heure d'ouverture, open, high, low, close.
Les horaires 01, 05, 09, 13, 17 sont dans le fuseau de la série fournie.
La décision de 09 h ne voit que les bougies closes à 09 h.
"""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
BASE=Path(__file__).resolve().parent

def score(frame,date,params):
    day=pd.Timestamp(date).normalize()
    cutoff=day+pd.Timedelta(hours=9)
    frame=frame[frame.index<cutoff].sort_index()
    if frame.index.has_duplicates:raise ValueError('Horodatages dupliqués')
    def get(group,hours):
        g=group.copy();g.index=g.index.hour
        return g.loc[hours] if set(hours).issubset(g.index) else None
    def amplitude(g):return (g.h.max()-g.l.min())/g.o.iloc[0]
    before=frame[frame.index<day]
    past=[]
    for dt,g in before.groupby(before.index.normalize()):
        if dt.weekday()>4:continue
        old=get(g,[1,5,9,13,17])
        if old is not None:past.append((amplitude(old.iloc[:2]),amplitude(old),old.h.max(),old.l.min()))
    now=get(frame[frame.index>=day],[1,5])
    if day.weekday()>4 or len(past)<20 or now is None:raise ValueError('20 séances antérieures et les bougies de 01 et 05 h du jour sont nécessaires')
    v=np.array(past[-20:]);hi=now.h.max();lo=now.l.min();c=now.c.iloc[-1]
    if hi<=lo or v[-1,2]<=v[-1,3] or np.median(v[:,0])<=0 or np.median(v[:,1])<=0:
        raise ValueError("Amplitude nulle dans les données")
    pl=np.clip((c-v[-1,3])/(v[-1,2]-v[-1,3]),-2,3)
    inp=np.array([np.log(amplitude(now)/np.median(v[:,0])), np.log(np.median(v[-3:,1])/np.median(v[:,1])),
        abs((c-now.o.iloc[0])/(hi-lo)),abs((2*c-hi-lo)/(hi-lo)),max(0,now.h.min()-now.l.max())/(hi-lo),
        max(0,pl-1,-pl)]+[int(day.weekday()==j) for j in range(4)])
    logits=np.array(params['intercept'])+np.array(params['coef'])@inp
    exp=np.exp(logits-logits.max());p=exp/exp.sum()
    value=p[params['classes'].index('calme')]
    return {'score_calme':float(value),'alerte_calme':bool(value>=params['cut']),'cassure_9h':('hausse' if c>now.h.iloc[0] and now.l.iloc[1]>=now.l.iloc[0] else 'baisse' if c<now.l.iloc[0] and now.h.iloc[1]<=now.h.iloc[0] else 'aucune')}
if __name__=='__main__':
    x=pd.read_csv(sys.argv[1],names=['ts','o','h','l','c'],parse_dates=['ts']).set_index('ts')
    if x.index.tz is not None:x.index=x.index.tz_localize(None)
    print(score(x,sys.argv[2],json.loads((BASE/'parametres.json').read_text())))
