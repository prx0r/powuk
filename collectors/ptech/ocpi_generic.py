"""Config-driven OCPI polling skeleton. Store raw responses before normalization.
Do not assume every CPO exposes identical paths/auth mechanics."""
from pathlib import Path
import requests, json, time
from base import RawStore

def poll_locations(source_id, url, headers=None, interval=60, once=False):
    store=RawStore(Path('data/raw'))
    while True:
        r=requests.get(url,headers=headers or {},timeout=30); r.raise_for_status()
        store.write(source_id,r.content,'json')
        if once:return r.json()
        time.sleep(interval)
