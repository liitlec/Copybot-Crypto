"""Banc mise (16/11, ecrit par la session de suivi) : mise du melange selon le regime connu avant la journee.
Normalise a la meme exposition moyenne. Usage : cd copy_sim/labo && python3 banc_mise.py"""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
import banc_or as B, banc_grille as G, banc_blocktrend as BT
from banc_melange import par_jour
m15,_=B.charge("xau_m15_50k"); m5,_=B.charge("xau_m5_90k")
debut=m5.index[0]; m15=m15[m15.index>=debut]
J={}
lr=np.log(m15["cloture"])
J["elan_m15"],_,_=par_jour(m15,np.sign(lr-lr.shift(12)),12)
ha,ba=m15["haut"].shift(1).rolling(48).max(),m15["bas"].shift(1).rolling(48).min()
J["cassure_m15"],_,_=par_jour(m15,(m15["cloture"]>ha).astype(float)-(m15["cloture"]<ba).astype(float),12)
r=np.log(m5["cloture"]).diff(); z=r/r.rolling(100).std().shift(1)
J["exces_m5"],_,_=par_jour(m5,(z>3).astype(float)-(z<-3).astype(float),3)
g=G.charge("xau_m5_90k"); P=BT.simule(g,0.25,0.6667,3)
atr=(m5["haut"].groupby(m5.index.floor("D")).max()-m5["bas"].groupby(m5.index.floor("D")).min()).rolling(20).mean().shift(1)
jb=pd.Series([p[3] for p in P],index=m5.index[[p[0] for p in P]].floor("D"))
stop=(0.6667*atr).reindex(jb.index).ffill().values
J["bt_or"]=(jb*stop).groupby(level=0).sum()
T=pd.DataFrame(J).fillna(0.0); T=T[T.index.dayofweek<5]
petites=T[["elan_m15","cassure_m15","exces_m5"]].sum(axis=1); bt=T["bt_or"]
D=m5.groupby(m5.index.floor("D")).agg(o=("cloture","first"),c=("cloture","last"),h=("haut","max"),b=("bas","min"))
D=D[D.index.dayofweek<5]
mv=((D.c-D.o).abs()/D.o).reindex(T.index); rg=((D.h-D.b)/D.o).reindex(T.index)
eff=((D.c-D.o).abs()/(D.h-D.b)).reindex(T.index)
tend=(mv>mv.median())
# infos connues avant le jour : veille
rg_v=rg.shift(1); calme_v=rg_v<rg_v.rolling(60,min_periods=20).median()
tend_v=tend.shift(1).fillna(False).astype(bool)
vol5=rg.shift(1).rolling(5).mean(); vol_haut=vol5>vol5.rolling(60,min_periods=20).median()
perf5=(petites+bt).shift(1).rolling(5).sum()
print("persistance : P(tendance demain | tendance aujourd'hui) = %.0f %%, base %.0f %%"%(100*tend[tend_v].mean(),100*tend.mean()))
print("P(tendance | volatilite 5 j haute) = %.0f %%"%(100*tend[vol_haut].mean()))
def bilan(nom,x):
    c=x.cumsum(); m=x.groupby(x.index.to_period("M")).sum()
    print("%-48s total %+7.0f $  mois<0 %2d/%d  pire creux %+6.0f $  $/jour %+5.1f"%(nom,x.sum(),(m<0).sum(),len(m),(c-c.cummax()).min(),x.mean()))
    return m
def norm(k):  # meme exposition moyenne que mise 1
    return k/k.mean()
base=petites+bt
M={}
M['base']=bilan("1. mise fixe (melange)",base)
p11=petites.where(~calme_v.fillna(False),0)
M['v11']=bilan("2. pause au calme (v11), mise fixe",p11+bt)
k=norm(np.where(vol_haut.fillna(False),2.0,0.5)); x=pd.Series(k,T.index)*(p11+bt)
M['vol']=bilan("3. x2 si volatilite 5 j haute, x0,5 sinon",x)
k=norm(np.where(tend_v,2.0,0.5)); x=pd.Series(k,T.index)*(p11+bt)
bilan("4. x2 si la veille etait une tendance",x)
k=norm(np.where(perf5.fillna(0)>0,2.0,0.5)); x=pd.Series(k,T.index)*(p11+bt)
bilan("5. x2 si le melange a gagne sur 5 j",x)
k=norm(np.where(tend,2.0,0.5)); x=pd.Series(k,T.index)*(p11+bt)
bilan("6. TRICHE : x2 les vrais jours de tendance",x)
print()
print("mois:", " ".join(str(p) for p in M['base'].index))
for n in ['base','v11','vol']: print(n, " ".join("%+.0f"%v for v in M[n].values))
print()
moit=T.index[len(T)//2]
for nom,k in [("v11",np.ones(len(T))),("vol",np.where(vol_haut.fillna(False),2.0,0.5)),("veille",np.where(tend_v,2.0,0.5))]:
    x=pd.Series(norm(k),T.index)*(p11+bt)
    print(nom,"1re moitie %+.0f  2e moitie %+.0f"%(x[x.index<moit].sum(),x[x.index>=moit].sum()))
    # petites seules vs bt seul
    print("   dont petites %+.0f  bt_or %+.0f"%((pd.Series(norm(k),T.index)*p11).sum(),(pd.Series(norm(k),T.index)*bt).sum()))
