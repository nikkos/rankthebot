SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query_text TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS query_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query_id INTEGER,
  query_text TEXT NOT NULL,
  llm TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  raw_response TEXT NOT NULL,
  FOREIGN KEY (query_id) REFERENCES queries(id)
);

CREATE TABLE IF NOT EXISTS parsed_mentions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query_run_id INTEGER NOT NULL,
  brand TEXT NOT NULL,
  position INTEGER NOT NULL,
  sentiment TEXT NOT NULL,
  context TEXT NOT NULL,
  FOREIGN KEY (query_run_id) REFERENCES query_runs(id)
);
"""
