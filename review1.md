# repair repo review1.md

> Structural issues to fix before adding more collectors.

---

## Critical fixes (in order)

### 1. Collectors not flowing through canonical garden
Current: collector → random JSONL → DONE
Should be: collector → raw archive → normalize → Observation → entity resolution → canonical store

### 2. Three competing schema systems
- schemas.py (FaultRecord, PartListing, etc.)
- ptech_schemas/canonical/*.schema.json
- core/ (Observation, Entity, etc.)
- shared/schema.sql

Make one canonical hierarchy.

### 3. PartListing conceptually wrong
Split into: Part (entity) + PartOffer (ephemeral) + Compatibility (relationship)

### 4. FaultRecord mixes four categories
Split into: FaultObservation + DerivedFact (prevalence) + PriceObservation + RepairEconomics

### 5. Kill all fake zeroes
Replace `float = 0` with `Optional[float] = None`

### 6. Storage path bug
DB_PATH resolves one directory above repo. Fix to explicit path.

### 7. UKGraph leakage
Planning/Land Registry don't belong in Repair. Remove.

### 8. AssetTransition abstraction
Not VALUE → ACTION, but AssetState → possible transitions → OutcomeDistribution

### 9. Need AssetFamily / AssetModel / AssetRevision / AssetInstance

### 10. RepairAttempt needs to be much richer (proprietary receipt)

### 11. Entity resolution needs explicit EntityResolution records

### 12. Observation IDs can collide semantically
Separate logical_observation_key from observation_content_hash

### 13. eBay collector needs redesign (stable IDs, state transitions)

### 14. Daemon lies about ingestion (rows_inserted ≠ actually inserted)

### 15. Raw collection must be immutable (no overwrites)

### 16. Rights/provenance too optional

### 17. Source priority upside down
Get 50 GPUs deeply resolved before 35 APIs dumping rows.

### 18. Missing: snapshots / cohorts (permanent panels)

---

## Target architecture

```
RAW SOURCES → immutable raw archive → NORMALIZERS → CANONICAL EVENTS
                                                        ↓
                                        ENTITY GRAPH ←→ OBSERVATION LOG
                                                        ↓
                                                    TRANSFORMS
                                                        ↓
                                    fault priors / market state / parts scarcity
                                                        ↓
                                                OPPORTUNITY MODEL
                                                        ↓
                                                ACTION / ROUTE
                                                        ↓
                                                REPAIR RECEIPT
                                                        ↓
                                                    OUTCOME
```

## Target entity graph

```
AssetFamily → AssetModel → AssetRevision → AssetInstance

Asset ──HAS_FAULT──► Fault
Fault ──REPAIRED_BY──► Intervention
Intervention ──USES──► Part
Part ──COMPATIBLE_WITH──► AssetRevision
Part ──HAS_OFFER──► PartOffer

AssetInstance → AssetState → AssetTransition → Outcome
```

---

## Implementation order

1. Freeze new collectors
2. Delete/consolidate competing storage paths
3. Choose one canonical schema contract
4. Fix DB path
5. Make raw ingestion immutable
6. Make collector → normalizer → validator → store pipeline real
7. Introduce AssetFamily / Model / Revision / Instance
8. Split Part from PartOffer from Compatibility
9. Split raw faults from derived fault rates/economics
10. Remove all fake numeric defaults
11. Upgrade RepairAttempt into proprietary receipt schema
12. Add explicit entity-resolution records
13. Make stable source-native/content-hash IDs
14. Build permanent cohorts
15. Remove Planning/Land Registry/Companies House from Repair
16. Get one complete GPU repair chain end-to-end
