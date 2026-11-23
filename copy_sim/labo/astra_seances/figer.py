from detecter import *
from score_matin import score
import json
bars=clean(pd.concat([read('ancien'),read('h4')]))
tr=features(bars,9).loc[:'2016']
f=features_market+calendar
m=fit(tr[f],tr.label)
s,lr=m.steps[0][1],m.steps[1][1]
coef=lr.coef_/s.scale_
obj=dict(classes=list(m.classes_),features=f,coef=coef.tolist(),intercept=(lr.intercept_-coef@s.mean_).tolist(),cut=float(np.quantile(m.predict_proba(tr[f])[:,list(m.classes_).index('calme')],.80)))
(BASE/'parametres.json').write_text(json.dumps(obj,indent=2))
# Exactitude du score sans bougies futures, y compris sur la deuxième source.
log=pd.read_csv(BASE/'journal.csv',parse_dates=['day']).query('hour==9').set_index('day')
h1=read('h1');h1.index=h1.index.tz_convert('UTC').tz_localize(None)
g=h1.resample('4h',origin='start_day',offset='1h');e=g.agg({'o':'first','h':'max','l':'min','c':'last'}).loc[g.size()==4]
for dt in [log.index[0],log.index[611],log.index[1302],log.index[-5]]:
    df=e if dt>bars.index[-1] else bars
    value=score(df.loc[dt-pd.Timedelta(days=65):],dt,obj)['score_calme']
    assert abs(value-log.loc[dt,'prob_calme'])<1.e-9
print('Score causal vérifié. Seuil',obj['cut'])
