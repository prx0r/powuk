from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

@dataclass
class RawStore:
    root: Path
    def write(self, source_id: str, body: bytes, suffix: str = "json") -> dict:
        now = datetime.now(timezone.utc)
        digest = hashlib.sha256(body).hexdigest()
        path = self.root/source_id/now.strftime("%Y/%m/%d")/f"{now.strftime('%H%M%S_%f')}_{digest[:16]}.{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {"raw_ref":str(path),"raw_hash":digest,"observed_at":now.isoformat()}

def append_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str)+'\n')
