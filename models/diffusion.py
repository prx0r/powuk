"""Technology diffusion forecasting kernel.

Uses a generalized Richards curve as a practical approximation to the
Bertalanffy-Richards family. It is intentionally lightweight; for production,
port/clone the authors' 2026 Bayesian replication code and preserve posterior
uncertainty rather than relying on point estimates.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit


def richards(t, K, r, t0, nu):
    t=np.asarray(t,dtype=float)
    nu=max(float(nu),1e-6)
    return K / np.power(1.0 + np.exp(-r*(t-t0)), 1.0/nu)


def fit_richards(t, y):
    t=np.asarray(t,float); y=np.asarray(y,float)
    if len(t)<5 or np.nanmax(y)<=0: raise ValueError('need >=5 positive observations')
    K0=max(np.nanmax(y)*1.5, np.nanmax(y)+1e-6)
    p0=[K0, 0.2, float(np.median(t)), 1.0]
    bounds=([np.nanmax(y),1e-6,np.nanmin(t)-100,0.05],[np.nanmax(y)*100+1e-6,10,np.nanmax(t)+100,20])
    popt, pcov=curve_fit(richards,t,y,p0=p0,bounds=bounds,maxfev=50000)
    return {'K':popt[0],'r':popt[1],'t0':popt[2],'nu':popt[3],'cov':pcov}


def forecast(t_hist, y_hist, t_future):
    fit=fit_richards(t_hist,y_hist)
    p=[fit[k] for k in ('K','r','t0','nu')]
    level=richards(np.asarray(t_future,float),*p)
    # numerical derivative = latent deployment/new-build rate
    eps=1e-3
    rate=(richards(np.asarray(t_future,float)+eps,*p)-richards(np.asarray(t_future,float)-eps,*p))/(2*eps)
    return {'fit':fit,'level':level,'deployment_rate':rate}
