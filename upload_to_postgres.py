import os
import json
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "192.168.1.28")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "video_convert")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DOCUMENTS_DIR = Path.home() / "Documents"
STATUS_FILES = ["convert.json", "streams.json"]


def find_status_file(name: str) -> Path:
    """Return path to status file regardless of case."""
    path = DOCUMENTS_DIR / name
    if path.exists():
        return path
    lower = name.lower()
    for candidate in DOCUMENTS_DIR.glob("*.json"):
        if candidate.name.lower() == lower:
            return candidate
    return path


def load_entries(path: Path):
    if not path.exists():
        print(f"Status log {path} not found")
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_tables(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS convert_log (
                time TIMESTAMP,
                filename TEXT,
                before_size BIGINT,
                after_size BIGINT,
                before_codec TEXT,
                after_codec TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS streams_log (
                time TIMESTAMP,
                filename TEXT,
                audio_stream TEXT,
                subtitle_stream TEXT
            );
            """
        )
    conn.commit()


def insert_convert(entries, conn):
    rows = []
    for e in entries:
        rows.append(
            (
                datetime.fromisoformat(e.get("time")),
                e.get("filename"),
                e.get("before_size"),
                e.get("after_size"),
                e.get("before_codec"),
                e.get("after_codec"),
            )
        )
    if not rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO convert_log (time, filename, before_size, after_size, before_codec, after_codec) VALUES %s",
            rows,
        )
    conn.commit()


def insert_streams(entries, conn):
    rows = []
    for e in entries:
        rows.append(
            (
                datetime.fromisoformat(e.get("time")),
                e.get("filename"),
                e.get("audio_stream"),
                e.get("subtitle_stream"),
            )
        )
    if not rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO streams_log (time, filename, audio_stream, subtitle_stream) VALUES %s",
            rows,
        )
    conn.commit()


def main():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    ensure_tables(conn)

    for fname in STATUS_FILES:
        path = find_status_file(fname)
        entries = load_entries(path)
        if not entries:
            print(f"No entries found in {path}")
            continue
        if fname.startswith("convert"):
            insert_convert(entries, conn)
        else:
            insert_streams(entries, conn)
        print(f"Uploaded {len(entries)} records from {fname} to PostgreSQL")
    conn.close()


if __name__ == "__main__":
    main()
