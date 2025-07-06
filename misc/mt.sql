PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE monkeytype_call_traces (
          created_at  REAL,
          module      TEXT,
          qualname    TEXT,
          arg_types   TEXT,
          return_type TEXT,
          yield_type  TEXT);
INSERT INTO monkeytype_call_traces VALUES(1751583124.6226820638,'monkeytype_sandbox.astmod','get_union_inner','{}','{"module": "monkeytype_sandbox.astmod", "qualname": "Union"}',NULL);
CREATE INDEX monkeytype_call_traces_module ON monkeytype_call_traces (module);
COMMIT;
