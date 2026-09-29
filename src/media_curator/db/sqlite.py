import fcntl
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS catalog(master_id INTEGER PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS media(
 id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, root TEXT NOT NULL,
 size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, device INTEGER NOT NULL, inode INTEGER NOT NULL,
 present INTEGER NOT NULL DEFAULT 1, data TEXT NOT NULL,
 quality TEXT NOT NULL DEFAULT 'Unknown', probe TEXT, probe_error TEXT,
 master_id INTEGER REFERENCES catalog(master_id), confidence REAL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'unmatched', candidates TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS decisions(
 media_id INTEGER PRIMARY KEY REFERENCES media(id), action TEXT NOT NULL,
 master_id INTEGER REFERENCES catalog(master_id), size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL,
 timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans(
 id TEXT PRIMARY KEY, created TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS operations(
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(id), created TEXT NOT NULL,
 status TEXT NOT NULL, manifest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS media_match ON media(master_id,status,present);
"""


def now() -> str:
    return datetime.now(UTC).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


@contextmanager
def connect(path: Path, *, lock: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)
    lockfile = None
    if lock:
        lockfile = path.with_suffix(path.suffix + ".lock").open("a")
        try:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            lockfile.close()
            raise RuntimeError("Another curator command is using this database") from exc
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    db.execute("PRAGMA synchronous=FULL")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
        if lockfile is not None:
            lockfile.close()


def event(db, kind: str, data):
    db.execute("INSERT INTO events(timestamp,kind,data) VALUES(?,?,?)", (now(), kind, dumps(data)))


def catalog_records(db):
    return [json.loads(r[0]) for r in db.execute("SELECT data FROM catalog ORDER BY master_id")]
