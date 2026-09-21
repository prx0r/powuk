"""Baseline production-network link reconstruction.

Mungo/Lafond/Farmer show industry, location and firm size are informative.
This implementation is deliberately generic: pass pairwise numeric features
and observed edge labels, then score candidate links.
"""
from __future__ import annotations
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

def fit_link_model(X,y):
    X=np.asarray(X,float); y=np.asarray(y,int)
    model=HistGradientBoostingClassifier(max_depth=6,learning_rate=0.08,max_iter=200,l2_regularization=1.0)
    model.fit(X,y)
    p=model.predict_proba(X)[:,1]
    return model, {'train_auc':float(roc_auc_score(y,p)) if len(np.unique(y))>1 else None}

def score_links(model,X):
    return model.predict_proba(np.asarray(X,float))[:,1]
