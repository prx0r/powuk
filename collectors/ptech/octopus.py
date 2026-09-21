import requests
BASE='https://api.octopus.energy/v1'
def products(available_at=None,page=1):
    p={'page':page}
    if available_at:p['available_at']=available_at
    r=requests.get(f'{BASE}/products/',params=p,timeout=30);r.raise_for_status();return r.json()
def unit_rates(product,tariff,period_from=None,period_to=None,page_size=1500):
    p={'page_size':page_size}
    if period_from:p['period_from']=period_from
    if period_to:p['period_to']=period_to
    url=f'{BASE}/products/{product}/electricity-tariffs/{tariff}/standard-unit-rates/'
    r=requests.get(url,params=p,timeout=30);r.raise_for_status();return r.json()
