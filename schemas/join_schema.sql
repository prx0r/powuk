CREATE TABLE federated_entity (
    entity_id           TEXT PRIMARY KEY,
    entity_type         TEXT NOT NULL,
    canonical_name      TEXT,
    source_gardens_json JSON NOT NULL,
    attributes_json     JSON
);

CREATE TABLE federated_edge (
    edge_id             TEXT PRIMARY KEY,
    subject_entity_id   TEXT NOT NULL,
    predicate           TEXT NOT NULL,
    object_entity_id    TEXT NOT NULL,
    valid_from          TIMESTAMP,
    valid_to            TIMESTAMP,
    observed_at         TIMESTAMP NOT NULL,
    confidence          DOUBLE NOT NULL,
    source_garden       TEXT NOT NULL,
    source_ids_json     JSON NOT NULL,
    rights              TEXT NOT NULL
);

CREATE TABLE event_link (
    event_link_id       TEXT PRIMARY KEY,
    from_event_id       TEXT NOT NULL,
    relation            TEXT NOT NULL, -- precedes|supports|confirms|contradicts|same_phenomenon|possible_cause
    to_event_id         TEXT NOT NULL,
    lag_seconds         BIGINT,
    confidence          DOUBLE,
    method_id           TEXT,
    method_version      TEXT,
    computed_at         TIMESTAMP
);
