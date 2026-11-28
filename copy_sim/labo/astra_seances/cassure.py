from detecter import read, clean, BASE
import pandas as pd
import numpy as np
def outcomes(df,source):
    rows=[]
    for day,g in df.groupby(df.index.normalize()):
        g=g.copy();g.index=g.index.hour
        if not {1,5,9,13,17}.issubset(g.index):continue
        for hour in [9,13]:
            prior=g.loc[1:hour-8];last=g.loc[hour-4]
            high=prior.h.max();low=prior.l.min();up=last.h>high;down=last.l<low
            if up==down:continue
            side=1 if up else -1
            accept=(last.c>high) if up else (last.c<low)
            signal=side if accept else -side
            rows.append([day,hour,'acceptée' if accept else 'rejetée',signal])
    return pd.DataFrame(rows,columns=['day','hour','cassure','sens'])
if __name__=='__main__':
    h=clean(pd.concat([read('ancien'),read('h4')]))
    h1=read('h1');h1.index=h1.index.tz_convert('UTC').tz_localize(None)
    g=h1.resample('4h',origin='start_day',offset='1h')
    db=g.agg({'o':'first','h':'max','l':'min','c':'last'}).loc[g.size()==4]
    sig=pd.concat([outcomes(h,'h4'),outcomes(db,'h1')])
    z=pd.read_csv(BASE/'decisions.csv',parse_dates=['day']).merge(sig,on=['day','hour'],how='left')
    z['bp_cassure']=10000*z.sens*z.net-4
    z.to_csv(BASE/'journal.csv',index=False)
    for (hour,period),q in z.groupby(['hour','period'],sort=False):
        print(hour,period)
        for name,b in q.dropna(subset=['cassure']).groupby('cassure'):
            print(name,len(b),round((b.bp_cassure>-4).mean(),2),round(b.bp_cassure.mean(),1),round((b.label=='tendance').mean(),2),round((b.label=='retour').mean(),2))
