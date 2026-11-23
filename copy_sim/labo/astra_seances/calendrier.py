from pathlib import Path
import pandas as pd
import numpy as np
root=Path(__file__).resolve().parent
fed=pd.read_csv(root/'fed.csv',parse_dates=['day']).day
d=pd.read_csv(root/'journal.csv',parse_dates=['day'])
for hour in [9,13]:
 z=d[d.hour==hour].copy()
 # Témoins de même jour de semaine et même mois civil. Pas de réunion programmée ces jours-là.
 z['fomc']=z.day.isin(fed)
 z['groupe']=z.day.dt.strftime('%Y-%m')+'-'+z.day.dt.dayofweek.astype(str)
 for c in ['calme','retour','tendance','mixte']:z[c]=(z.label==c).astype(float)
 variables=['calme','retour','tendance','mixte','post','t','r','fixe']
 ref=z[~z.fomc].groupby('groupe')[variables].mean().add_prefix('ref_')
 e=z[z.fomc].join(ref,on='groupe')
 e.to_csv(root/f'fed_{hour}h.csv',index=False)
 for k,v in [(k,v) for k,v in e.groupby('period',sort=False)]+[('ensemble',e)]:
    print(hour,k,len(v),v.label.value_counts().to_dict(),'refs',v[['ref_calme','ref_retour','ref_tendance']].mean().round(3).to_dict(),'relAmplitude',round((v.post/v.ref_post).median(),2),'T/R',v[['t','r']].mean().round(2).to_dict())
