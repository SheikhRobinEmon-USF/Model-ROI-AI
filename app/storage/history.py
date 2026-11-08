"""Transactional local history and compact benchmark measurements."""
from contextlib import contextmanager
import json
import logging
import os
from pathlib import Path
import sqlite3
from uuid import UUID


def directory():
    path = Path(os.environ.get("MODELROI_HISTORY_DIR", str(Path.home() / ".modelroi" / "runs")))
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def _write(db, report):
    run_id = str(UUID(report["run_id"]))
    summary = {key: report[key] for key in ("run_id", "started_at", "model_id")}
    if report.get("evidence_type") == "custom_prompt":
        summary.update(title=" ".join(report["prompt"].split())[:75], parent_id=report.get("parent_id"),
                       chat_name=report.get("chat_name"), pinned=report.get("pinned"))
    db.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?)", (
        run_id, report["started_at"], json.dumps(summary), json.dumps(report, allow_nan=False)))
    db.execute("DELETE FROM measurements WHERE run_id=?", (run_id,))
    for run in report.get("runs", [report]):
        rows = run.get("results", [])
        db.executemany("INSERT INTO measurements VALUES (?, ?, ?, ?, ?)", (
            (run_id, run["model_id"], int(bool(row.get("passed"))),
             (row.get("judge") or {}).get("score"), row.get("latency_ms") if row.get("status") == "completed" else None)
            for row in rows))
    return run_id


@contextmanager
def connection():
    folder = directory()
    db = sqlite3.connect(folder / "history.sqlite3", timeout=30)
    try:
        if db.execute("PRAGMA user_version").fetchone()[0] == 0:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("PRAGMA user_version").fetchone()[0] == 0:
                db.execute("CREATE TABLE runs(id TEXT PRIMARY KEY, started TEXT, summary TEXT, report TEXT)")
                db.execute("CREATE INDEX recent ON runs(started DESC)")
                db.execute("CREATE TABLE measurements(run_id TEXT, model TEXT, passed INTEGER, score REAL, latency REAL)")
                db.execute("CREATE INDEX by_run ON measurements(run_id)")
                for path in folder.glob("*.json"):
                    try:
                        report = json.loads(path.read_text())
                        if str(UUID(path.stem)) != report["run_id"]:
                            raise ValueError("Run ID mismatch")
                    except (ValueError, KeyError, TypeError) as exc:
                        logging.warning("Skipping invalid legacy report %s: %s", path.name, exc)
                        continue
                    _write(db, report)
                db.execute("PRAGMA user_version=1")
            db.commit()
        with db:
            yield db
    finally:
        db.close()


def save(result):
    with connection() as db:
        return _write(db, result)


def load(run_id):
    key = str(UUID(run_id))
    with connection() as db:
        row = db.execute("SELECT report FROM runs WHERE id=?", (key,)).fetchone()
    if row is None:
        raise FileNotFoundError(key)
    return json.loads(row[0])


def list_runs():
    with connection() as db:
        return [json.loads(row[0]) for row in db.execute("SELECT summary FROM runs ORDER BY started DESC")]


def delete_chat(leaf):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        records = [json.loads(r[0]) for r in db.execute("SELECT summary FROM runs")]
        chats = {r["run_id"]: r for r in records if "title" in r}
        children = {}
        for row in chats.values():
            children.setdefault(row["parent_id"], set()).add(row["run_id"])
        removed = []
        while leaf in chats and not children.get(leaf):
            parent = chats[leaf]["parent_id"]
            removed.append(leaf)
            children[parent].discard(leaf)
            leaf = parent
        for key in removed:
            (directory() / f"{UUID(key)}.json").unlink(missing_ok=True)
            db.execute("DELETE FROM runs WHERE id=?", (key,))
    return removed


def benchmark_analytics():
    # Import only on a dashboard request; the offline query needs no DuckDB extensions.
    import duckdb
    with connection() as db, duckdb.connect(config={"threads": 1, "memory_limit": "128MB"}) as analysis:
        analysis.execute("CREATE TABLE cases(run_id VARCHAR, model VARCHAR, passed INTEGER, score DOUBLE, latency DOUBLE)")
        rows = db.execute("SELECT run_id, model, passed, score, latency FROM measurements")
        while batch := rows.fetchmany(1000):
            analysis.execute("""
                INSERT INTO cases SELECT unnest(?::VARCHAR[]), unnest(?::VARCHAR[]),
                    unnest(?::INTEGER[]), unnest(?::DOUBLE[]), unnest(?::DOUBLE[])
            """, [list(column) for column in zip(*batch)])
        result = analysis.execute("""
            SELECT model, count(DISTINCT run_id) AS runs, count(*) AS attempts,
                   sum(passed) AS passed, count(score) AS graded, avg(score) AS mean_grade,
                   median(latency) AS median_ms
            FROM cases GROUP BY model ORDER BY model
        """)
        keys = [col[0] for col in result.description]
        return [dict(zip(keys, row)) for row in result.fetchall()]
