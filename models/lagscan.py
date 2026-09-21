"""Lead/lag screening for candidate causal-assimilation edges.

This is a discovery screen, not causal proof. Use PCMCI+/J-PCMCI+ once data
volume and dimensionality justify it; validate candidate edges out of sample.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import pearsonr
try:
    from statsmodels.tsa.stattools import grangercausalitytests
except Exception:
    grangercausalitytests=None

def lag_scan(x,y,max_lag=30,min_n=12):
    x=np.asarray(x,float); y=np.asarray(y,float)
    out=[]
    for lag in range(-max_lag,max_lag+1):
        if lag>0: a,b=x[:-lag],y[lag:]
        elif lag<0: a,b=x[-lag:],y[:lag]
        else: a,b=x,y
        ok=np.isfinite(a)&np.isfinite(b)
        if ok.sum()<min_n: continue
        r,p=pearsonr(a[ok],b[ok])
        out.append({'lag':lag,'r':float(r),'p':float(p),'n':int(ok.sum())})
    return sorted(out,key=lambda z:abs(z['r']),reverse=True)

def granger_screen(x,y,max_lag=10):
    if grangercausalitytests is None: return []
    z=np.column_stack([np.asarray(y,float),np.asarray(x,float)])
    z=z[np.isfinite(z).all(axis=1)]
    if len(z)<max_lag*4+10: return []
    tests=grangercausalitytests(z,maxlag=max_lag,verbose=False)
    out=[]
    for lag,v in tests.items():
        stat,p,df1,df2=v[0]['ssr_ftest']
        out.append({'lag':lag,'F':float(stat),'p':float(p),'df1':df1,'df2':df2})
    return out
