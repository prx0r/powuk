"""Companies House streaming collector: long-running HTTP, NOT WebSocket.
Raw-line-first and cursor-resumable."""
import os, json, requests
from pathlib import Path
from base import RawStore, append_jsonl
BASE='https://stream.companieshouse.gov.uk/companies'

def run(raw_root=Path('data/raw'),norm=Path('data/normalized/company_events.jsonl'),cursor_file=Path('data/state/ch_timepoint.txt')):
    key=os.environ['COMPANIES_HOUSE_API_KEY']
    cursor=cursor_file.read_text().strip() if cursor_file.exists() else None
    params={'timepoint':cursor} if cursor else {}
    store=RawStore(raw_root)
    with requests.get(BASE,params=params,auth=(key,''),stream=True,timeout=(30,None)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line: continue
            meta=store.write('companies_house_stream',line,'json')
            obj=json.loads(line)
            event=obj.get('event') or {}
            rec={**meta,'company_number':obj.get('company_number'),'event_type':event.get('type'),'fields_changed':event.get('fields_changed') or [],'published_at':event.get('published_at'),'timepoint':event.get('timepoint'),'payload':obj}
            append_jsonl(norm,rec)
            if rec['timepoint']:
                cursor_file.parent.mkdir(parents=True,exist_ok=True); cursor_file.write_text(str(rec['timepoint']))
if __name__=='__main__': run()
