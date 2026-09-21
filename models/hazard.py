"""Installed-base cohort -> future maintenance demand."""
from __future__ import annotations
import numpy as np

def maintenance_demand(new_installations, hazard_by_age, parts_per_failure=1.0):
    installs=np.asarray(new_installations,float)
    h=np.asarray(hazard_by_age,float)
    # convolution: cohort installed at t contributes failures at t+age
    failures=np.convolve(installs,h)[:len(installs)]
    return failures*float(parts_per_failure)

def weibull_hazard(age, shape, scale):
    age=np.asarray(age,float)
    a=np.maximum(age,1e-9)
    return (shape/scale)*np.power(a/scale,shape-1)
