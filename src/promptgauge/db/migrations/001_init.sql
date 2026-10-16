-- 001_init.sql: every table in PRD §12. SQLite; applied once by Migrator.
-- "case" and "index" are SQL keywords, so they are quoted wherever they appear.

CREATE TABLE IF NOT EXISTS experiment (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT    NOT NULL CHECK (kind IN ('eval', 'ablation')),
    name           TEXT,
    prompt_hash    TEXT    NOT NULL,
    prompt_text    TEXT    NOT NULL,
    dataset_hash   TEXT    NOT NULL,
    model          TEXT    NOT NULL,
    judge          TEXT    NOT NULL,
    config_json    TEXT    NOT NULL,
    status         TEXT    NOT NULL CHECK (status IN ('running', 'done', 'partial', 'stopped')),
    stopped_reason TEXT,
    created_at     TEXT    NOT NULL,
    finished_at    TEXT
);

CREATE TABLE IF NOT EXISTS "case" (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_hash TEXT    NOT NULL,
    "index"      INTEGER NOT NULL,
    input        TEXT    NOT NULL,
    expected     TEXT,
    context      TEXT,
    tags_json    TEXT    NOT NULL DEFAULT '[]',
    created_at   TEXT    NOT NULL,
    UNIQUE (dataset_hash, "index")
);

-- One row per call made, cached or not (F2.6). The same hash can appear in several
-- experiments (a cache hit in a later run), so the hash is indexed rather than the key.
CREATE TABLE IF NOT EXISTS call (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    hash          TEXT    NOT NULL,
    model         TEXT    NOT NULL,
    system_hash   TEXT    NOT NULL,
    input_hash    TEXT    NOT NULL,
    temperature   REAL    NOT NULL,
    repeat_index  INTEGER NOT NULL,
    output        TEXT    NOT NULL,
    input_tokens  INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd      REAL    NOT NULL,
    cached        INTEGER NOT NULL CHECK (cached IN (0, 1)),
    experiment_id INTEGER NOT NULL REFERENCES experiment (id),
    created_at    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS call_hash ON call (hash);
CREATE INDEX IF NOT EXISTS call_experiment ON call (experiment_id);

CREATE TABLE IF NOT EXISTS result (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL REFERENCES experiment (id),
    case_id       INTEGER NOT NULL REFERENCES "case" (id),
    repeat_index  INTEGER NOT NULL,
    variant_id    INTEGER,            -- NULL = baseline prompt; otherwise the segment removed
    scorer        TEXT    NOT NULL,
    score         REAL,               -- NULL = judge failed
    reason        TEXT,
    call_hash     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS result_experiment ON result (experiment_id);

CREATE TABLE IF NOT EXISTS segment (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id     INTEGER NOT NULL REFERENCES experiment (id),
    parent_segment_id INTEGER REFERENCES segment (id),
    level             TEXT    NOT NULL CHECK (level IN ('block', 'line')),
    "index"           INTEGER NOT NULL,
    start_offset      INTEGER NOT NULL,
    end_offset        INTEGER NOT NULL,
    text              TEXT    NOT NULL,
    tokens            INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS segment_experiment ON segment (experiment_id);

CREATE TABLE IF NOT EXISTS verdict (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL REFERENCES experiment (id),
    segment_id    INTEGER NOT NULL UNIQUE REFERENCES segment (id),
    mean_delta    REAL    NOT NULL,
    ci_low        REAL    NOT NULL,
    ci_high       REAL    NOT NULL,
    n_cases       INTEGER NOT NULL,
    verdict       TEXT    NOT NULL CHECK (verdict IN ('red', 'grey', 'green')),
    stage         INTEGER NOT NULL CHECK (stage IN (1, 2))
);
CREATE INDEX IF NOT EXISTS verdict_experiment ON verdict (experiment_id);

CREATE TABLE IF NOT EXISTS ablation (
    experiment_id INTEGER PRIMARY KEY REFERENCES experiment (id),
    baseline_score REAL    NOT NULL,
    cut_score      REAL,
    cut_ci_low     REAL,
    cut_ci_high    REAL,
    cut_prompt     TEXT    NOT NULL,
    tokens_before  INTEGER NOT NULL,
    tokens_after   INTEGER NOT NULL,
    confirmed      INTEGER NOT NULL CHECK (confirmed IN (0, 1))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
