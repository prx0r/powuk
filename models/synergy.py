"""PID-inspired complementarity screening.

This is NOT exact Partial Information Decomposition. It is a cheap first-pass
screen that asks whether an interaction term materially improves out-of-sample
prediction beyond the additive inputs. Exact PID should be a later optional
model for shortlisted relationships.
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

def interaction_uplift(x1,x2,y,splits=5):
    x1=np.asarray(x1,float); x2=np.asarray(x2,float); y=np.asarray(y,float)
    ok=np.isfinite(x1)&np.isfinite(x2)&np.isfinite(y)
    x1,x2,y=x1[ok],x2[ok],y[ok]
    if len(y)<30: raise ValueError('need >=30 aligned observations')
    base=np.column_stack([x1,x2])
    inter=np.column_stack([x1,x2,x1*x2])
    cv=TimeSeriesSplit(n_splits=min(splits,max(2,len(y)//10)))
    model=lambda: make_pipeline(StandardScaler(),Ridge(alpha=1.0))
    b=-cross_val_score(model(),base,y,cv=cv,scoring='neg_mean_squared_error').mean()
    i=-cross_val_score(model(),inter,y,cv=cv,scoring='neg_mean_squared_error').mean()
    uplift=(b-i)/max(abs(b),1e-12)
    return {'mse_additive':float(b),'mse_interaction':float(i),'interaction_uplift':float(uplift)}
