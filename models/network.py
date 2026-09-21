"""Linear production-network propagation utilities."""
from __future__ import annotations
import numpy as np

def leontief_inverse(A):
    A=np.asarray(A,float)
    if A.shape[0]!=A.shape[1]: raise ValueError('A must be square')
    return np.linalg.inv(np.eye(A.shape[0])-A)

def final_demand_response(A, final_demand_shock):
    """Gross-output response x=(I-A)^-1 d."""
    return leontief_inverse(A) @ np.asarray(final_demand_shock,float)

def upstream_exposure(A, target_index):
    """Total direct+indirect gross-output requirement for one unit final demand."""
    n=len(A); d=np.zeros(n); d[target_index]=1.0
    return final_demand_response(A,d)
