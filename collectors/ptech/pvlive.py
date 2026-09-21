from pathlib import Path
import requests, json
BASE='https://api.pvlive.uk/pvlive/api/v4'

def fetch_gsp(gsp_id=0,start=None,end=None,extra_fields='capacity_mwp,installedcapacity_mwp,updated_gmt'):
    p={'data_format':'json','extra_fields':extra_fields}
    if start: p['start']=start
    if end: p['end']=end
    r=requests.get(f'{BASE}/gsp/{gsp_id}',params=p,timeout=60); r.raise_for_status(); return r.json()
if __name__=='__main__': print(json.dumps(fetch_gsp(),indent=2))
