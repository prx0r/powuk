"""Backfill Open Repair Alliance aggregate and release metadata.
Run from a machine with internet access."""
from pathlib import Path
import requests
URL='https://raw.githubusercontent.com/openrepair/data/master/aggregated/202507/OpenRepairData_v0.3_aggregate_202507.csv'

def backfill(out=Path('data/raw/open_repair/202507.csv')):
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        with out.open('wb') as f:
            for chunk in r.iter_content(1024*1024):
                if chunk: f.write(chunk)
    return out
if __name__=='__main__': print(backfill())
