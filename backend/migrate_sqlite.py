"""Add missing ArchVision columns to local SQLite DB (create_all does not alter existing tables)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "blueprint_reader.db"

# table -> list of (column, sqlite type clause)
ALTERS = {
    "analysis_versions": [
        ("user_id", "TEXT"),
        ("file_path", "TEXT"),
        ("file_name", "TEXT"),
        ("file_type", "TEXT"),
        ("progress", "INTEGER DEFAULT 0"),
        ("current_stage", "TEXT"),
        ("error_message", "TEXT"),
        ("retry_of_job_id", "TEXT"),
        ("started_at", "TEXT"),
    ],
    "rooms": [
        ("is_user_corrected", "INTEGER DEFAULT 0"),
    ],
    "openings": [
        ("is_user_corrected", "INTEGER DEFAULT 0"),
    ],
}


def main() -> None:
    if not DB_PATH.exists():
        print(f"No DB at {DB_PATH}; nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    tables = {
        r[0]
        for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    print("Existing tables:", sorted(tables))

    for table, cols in ALTERS.items():
        if table not in tables:
            print(f"Skip {table} (missing)")
            continue
        existing = {
            r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, decl in cols:
            if name in existing:
                print(f"OK {table}.{name}")
                continue
            sql = f"ALTER TABLE {table} ADD COLUMN {name} {decl}"
            print("RUN", sql)
            cur.execute(sql)

    conn.commit()
    conn.close()
    print("SQLite migration complete.")


if __name__ == "__main__":
    main()
