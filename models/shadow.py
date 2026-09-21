"""Constraint pressure and LP shadow prices."""
from __future__ import annotations
import numpy as np
from scipy.optimize import linprog

def pressure(load, supply, inventory=0.0, substitute_capacity=0.0, substitute_discount=1.0, eps=1e-12):
    effective=float(supply)+float(inventory)+float(substitute_capacity)*float(substitute_discount)
    return float(load)/max(effective,eps)

def shadow_prices(resource_by_activity, resource_supply, activity_value=None):
    """Maximize weighted activity under physical resource constraints.

    resource_by_activity[i,j] = units of resource i consumed by activity j.
    scipy minimizes, so objective is negated. HiGHS returns inequality duals;
    sign is flipped to report marginal objective gain from +1 unit supply.
    """
    B=np.asarray(resource_by_activity,float)
    s=np.asarray(resource_supply,float)
    n=B.shape[1]
    c=np.ones(n) if activity_value is None else np.asarray(activity_value,float)
    res=linprog(-c,A_ub=B,b_ub=s,bounds=[(0,None)]*n,method='highs')
    if not res.success: raise RuntimeError(res.message)
    dual=-np.asarray(res.ineqlin.marginals,float)
    slack=np.asarray(res.ineqlin.residual,float)
    return {'activity':res.x,'objective':float(c@res.x),'shadow_price':dual,'slack':slack}
