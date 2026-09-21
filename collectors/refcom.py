"""
REFCOM F-gas collector — HVAC/refrigeration capacity.
Uses REFCOM public REST API (no auth needed).
"""

import json
import urllib.request
from typing import List
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.companies_house import search_companies, get_company
from shared.collector_contract import Collector, RawBatch
from shared.schema import Observation, Entity, TruthClass, Recoverability
from shared.storage import (
    archive_raw, store_entity, store_observation, store_raw_ingest,
    store_collector_run, get_db, init_db
)


class REFCOMCollector(Collector):
    source_id = "refcom"
    
    def collect(self) -> RawBatch:
        """Fetch F-gas certified company count and sample."""
        base_url = "https://api.refcom.org.uk/api/PublicCompany"
        
        # Get total count
        count_url = f"{base_url}/GetFgasActiveCertificateCount"
        req = urllib.request.Request(count_url, headers={"User-Agent": "powuk/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_count = int(resp.read().decode().strip())
        
        # Get first page of companies
        companies = []
        for idx in range(0, min(100, total_count), 10):
            url = f"{base_url}/GetByIndex?scheme=fgas&index={idx}"
            req = urllib.request.Request(url, headers={"User-Agent": "powuk/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                    if data:
                        companies.append(data)
            except Exception:
                break
        
        result = {
            "total_count": total_count,
            "sample": companies,
            "scheme": "fgas",
        }
        
        return RawBatch(
            source_id=self.source_id,
            dataset="fgas_companies",
            data=json.dumps(result).encode(),
            record_count=total_count,
            metadata={"base_url": base_url}
        )
    
    def normalize(self, raw: RawBatch) -> list:
        observations = []
        data = json.loads(raw.data)
        
        # Store total count
        obs = Observation(
            observation_id="",
            garden="powuk",
            source_id=self.source_id,
            entity_id="fgas_companies",
            metric="fgas_active_companies",
            value_numeric=float(data["total_count"]),
            unit="companies",
            event_time=datetime.now(timezone.utc).isoformat(),
            truth_class=TruthClass.OBSERVED,
            recoverability=Recoverability.SNAPSHOT,
        )
        observations.append(obs)
        
        return observations


def run_collector():
    init_db()
    collector = REFCOMCollector()
    manifest = collector.run()
    with get_db() as conn:
        store_collector_run(conn, manifest.run_id, manifest.source_id,
                          manifest.raw_records, manifest.normalized_records,
                          manifest.new_observations, manifest.status, manifest.error)
    print(json.dumps({"source": manifest.source_id, "status": manifest.status,
                      "raw": manifest.raw_records, "norm": manifest.normalized_records}, indent=2))
    return manifest


if __name__ == "__main__":
    run_collector()
