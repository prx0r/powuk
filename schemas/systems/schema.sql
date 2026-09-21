CREATE TABLE watched_entity (
    watched_entity_id      TEXT PRIMARY KEY,
    name                   TEXT NOT NULL,
    entity_type            TEXT, -- company|lab|project|repo|topic
    domain                 TEXT,
    aliases_json           JSON,
    urls_json              JSON,
    active                 BOOLEAN DEFAULT TRUE
);

CREATE TABLE research_work (
    work_id                 TEXT PRIMARY KEY,
    doi                     TEXT,
    openalex_id             TEXT,
    title                   TEXT,
    published_at            TIMESTAMP,
    updated_at              TIMESTAMP,
    authors_json            JSON,
    institutions_json       JSON,
    topics_json             JSON,
    abstract_or_summary     TEXT,
    source_ids_json         JSON
);

CREATE TABLE repo_event (
    repo_event_id           TEXT PRIMARY KEY,
    repo_full_name          TEXT,
    event_type              TEXT, -- release|commit|tag|repo_created
    event_time              TIMESTAMP,
    observed_at             TIMESTAMP,
    sha_or_tag              TEXT,
    title                   TEXT,
    body                    TEXT,
    source_url              TEXT
);

CREATE TABLE patent_event (
    patent_event_id         TEXT PRIMARY KEY,
    publication_number      TEXT,
    family_id               TEXT,
    applicant_json          JSON,
    inventors_json          JSON,
    cpc_json                JSON,
    publication_date        DATE,
    priority_date           DATE,
    legal_status            TEXT,
    title                   TEXT,
    abstract                TEXT,
    observed_at             TIMESTAMP,
    source_id               TEXT
);

CREATE TABLE frontier_event (
    frontier_event_id       TEXT PRIMARY KEY,
    event_time              TIMESTAMP,
    observed_at             TIMESTAMP NOT NULL,
    domain                  TEXT,
    event_class             TEXT,
    title                   TEXT,
    source_entity_ids_json  JSON,
    claimed_constraint      TEXT,
    measured_claims_json    JSON,
    evidence_ids_json       JSON,
    materiality_score       DOUBLE,
    confidence              DOUBLE
);

CREATE TABLE seesaw_hypothesis (
    hypothesis_id           TEXT PRIMARY KEY,
    created_at              TIMESTAMP NOT NULL,
    status                  TEXT NOT NULL,
    innovation              TEXT NOT NULL,
    constraint_relaxed      TEXT NOT NULL,
    new_constraint          TEXT,
    affected_entities_json  JSON,
    affected_resources_json JSON,
    predictions_json        JSON NOT NULL,
    kill_conditions_json    JSON NOT NULL,
    source_event_ids_json   JSON NOT NULL,
    hypothesis_version      TEXT NOT NULL
);

CREATE TABLE hypothesis_evidence (
    hypothesis_id           TEXT NOT NULL,
    evidence_event_id       TEXT NOT NULL,
    target_id               TEXT NOT NULL, -- prediction or kill ID
    relation                TEXT NOT NULL, -- support|contradict|trigger|irrelevant
    probability             DOUBLE NOT NULL,
    decision_spec_id        TEXT,
    decision_version        TEXT,
    observed_at             TIMESTAMP NOT NULL,
    PRIMARY KEY(hypothesis_id, evidence_event_id, target_id)
);
