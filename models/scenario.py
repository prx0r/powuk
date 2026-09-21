"""Simple technology-shock -> component/skill/maintenance scenario engine."""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from .shadow import pressure

def run_scenario(spec: dict):
    adoption=float(spec['technology']['baseline_new_units'])*(1.0+float(spec['technology'].get('growth_shock',0)))
    components=[]
    for c in spec.get('components',[]):
        load=adoption*float(c.get('units_per_tech',0))+float(c.get('maintenance_load',0))
        p=pressure(load,c.get('capacity',0),c.get('inventory',0),c.get('substitute_capacity',0),c.get('substitute_discount',1))
        components.append({**c,'projected_load':load,'pressure':p})
    skills=[]
    for s in spec.get('skills',[]):
        req=adoption*float(s.get('workers_per_tech',0))
        eff=float(s.get('incumbent',0))+float(s.get('adjacent_convertible',0))*float(s.get('mobility_rate',0))+float(s.get('training_pipeline',0))
        skills.append({**s,'required':req,'effective_supply':eff,'pressure':req/max(eff,1e-9)})
    components.sort(key=lambda x:x['pressure'],reverse=True)
    skills.sort(key=lambda x:x['pressure'],reverse=True)
    return {'projected_new_units':adoption,'components':components,'skills':skills}

def run_file(path):
    with open(path) as f: return run_scenario(json.load(f))
