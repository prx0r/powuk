-- Shared export contract. Domain schemas live inside systems/*.

CREATE TABLE entity (
    entity_id           TEXT PRIMARY KEY,
    entity_type         TEXT NOT NULL,
    canonical_name      TEXT NOT NULL,
    created_at          TIMESTAMP NOT NULL,
    attributes_json     JSON
);

CREATE TABLE entity_alias (
    alias_id             TEXT PRIMARY KEY,
    entity_id            TEXT NOT NULL,
    namespace            TEXT NOT NULL,  -- gtin, mpn, lei, figi, soc2020, eprel, company_number...
    alias_value          TEXT NOT NULL,
    valid_from           TIMESTAMP,
    valid_to             TIMESTAMP,
    confidence           DOUBLE DEFAULT 1.0,
    source_id            TEXT,
    UNIQUE(namespace, alias_value, entity_id)
);

CREATE TABLE observation (
    observation_id       TEXT PRIMARY KEY,
    garden               TEXT NOT NULL,
    entity_id            TEXT NOT NULL,
    metric               TEXT NOT NULL,
    value_json           JSON NOT NULL,
    unit                 TEXT,
    event_time            TIMESTAMP NOT NULL,
    observed_at           TIMESTAMP NOT NULL,
    source_id             TEXT NOT NULL,
    source_version        TEXT,
    truth_class           TEXT NOT NULL,
    recoverability        TEXT NOT NULL,
    rights                TEXT NOT NULL,
    raw_payload_hash      TEXT,
    method_id             TEXT,
    method_version        TEXT,
    parent_ids_json       JSON,
    tags_json             JSON
);

CREATE INDEX idx_observation_entity_metric_time
ON observation(entity_id, metric, event_time);

CREATE TABLE derived_fact (
    derived_id            TEXT PRIMARY KEY,
    garden                TEXT NOT NULL,
    entity_id             TEXT NOT NULL,
    metric                TEXT NOT NULL,
    value_json            JSON NOT NULL,
    unit                  TEXT,
    computed_at           TIMESTAMP NOT NULL,
    valid_from            TIMESTAMP,
    valid_to              TIMESTAMP,
    method_id             TEXT NOT NULL,
    method_version        TEXT NOT NULL,
    input_ids_json        JSON NOT NULL,
    truth_class           TEXT NOT NULL,
    confidence            DOUBLE NOT NULL,
    rights                TEXT NOT NULL,
    limitations_json      JSON
);

CREATE TABLE economic_event (
    event_id              TEXT PRIMARY KEY,
    garden                TEXT NOT NULL,
    event_type            TEXT NOT NULL,
    observed_at           TIMESTAMP NOT NULL,
    effective_at          TIMESTAMP,
    entity_ids_json       JSON NOT NULL,
    direction             TEXT,
    magnitude             DOUBLE,
    confidence            DOUBLE NOT NULL,
    source_ids_json       JSON NOT NULL,
    evidence_ids_json     JSON,
    rights                TEXT NOT NULL,
    tags_json             JSON
);

CREATE TABLE relationship (
    relationship_id       TEXT PRIMARY KEY,
    subject_entity_id     TEXT NOT NULL,
    predicate             TEXT NOT NULL,
    object_entity_id      TEXT NOT NULL,
    observed_at           TIMESTAMP NOT NULL,
    valid_from            TIMESTAMP,
    valid_to              TIMESTAMP,
    confidence            DOUBLE NOT NULL,
    source_ids_json       JSON NOT NULL,
    rights                TEXT NOT NULL,
    attributes_json       JSON
);
