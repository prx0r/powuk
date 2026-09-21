"""Skill bottleneck model with adjacent-worker mobility and training throughput."""
from __future__ import annotations
import numpy as np

def skill_pressure(required_workers, incumbent_workers, mobility_matrix=None, adjacent_workers=None,
                   training_completions=0.0, mobility_discount=0.5, eps=1e-9):
    req=np.asarray(required_workers,float)
    supply=np.asarray(incumbent_workers,float).copy()
    if mobility_matrix is not None and adjacent_workers is not None:
        M=np.asarray(mobility_matrix,float)
        adj=np.asarray(adjacent_workers,float)
        supply += float(mobility_discount)*(M.T @ adj)
    supply += np.asarray(training_completions,float)
    return req/np.maximum(supply,eps)

def training_gap(required_workers,effective_supply,completion_rate,months_to_qualify=12):
    gap=np.maximum(np.asarray(required_workers,float)-np.asarray(effective_supply,float),0)
    pipeline=np.asarray(completion_rate,float)*float(months_to_qualify)/12.0
    return np.maximum(gap-pipeline,0)
