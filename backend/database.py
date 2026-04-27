import os
import sqlite3
import pathlib

_ROOT = pathlib.Path(__file__).parent.parent
# DATA_DIR kann per Env-Variable überschrieben werden (z.B. Docker-Volume)
_DATA_DIR   = pathlib.Path(os.environ.get("DATA_DIR", str(_ROOT)))
DB_PATH     = _DATA_DIR / "racecontrol.db"
SCHEMA_PATH = _ROOT / "schema.sql"


def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Migration BEFORE executescript so views are recreated cleanly afterwards
    _migrate(conn)
    conn.commit()
    # Apply full schema (CREATE TABLE/VIEW IF NOT EXISTS — safe to re-run)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # Set admin password if still placeholder (fresh DB or Docker first start)
    _init_admin_password(conn)
    conn.close()


def _init_admin_password(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT password_hash FROM Users WHERE username = 'admin'"
    ).fetchone()
    if row and row[0] == "__CHANGE_ON_FIRST_LOGIN__":
        from auth import hash_password
        conn.execute(
            "UPDATE Users SET password_hash = ? WHERE username = 'admin'",
            (hash_password("admin"),),
        )
        conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Bring existing databases up to current schema without data loss."""
    _migrate_participants(conn)
    _migrate_classes(conn)
    _migrate_classes_status(conn)
    _migrate_classes_exhibition(conn)
    _migrate_events(conn)
    _migrate_participants_unique_per_class(conn)


def _migrate_events(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(Events)")}
    if not existing:
        return
    if "description" not in existing:
        conn.execute("ALTER TABLE Events ADD COLUMN description TEXT")


def _migrate_participants(conn: sqlite3.Connection) -> None:
    col_info = {row[1]: {"notnull": row[3]}
                for row in conn.execute("PRAGMA table_info(Participants)")}

    if not col_info:
        return  # fresh DB — executescript will create the table

    # Simple column additions
    if "fee_paid" not in col_info:
        conn.execute("ALTER TABLE Participants ADD COLUMN fee_paid INTEGER NOT NULL DEFAULT 0")
    if "helmet_ok" not in col_info:
        conn.execute("ALTER TABLE Participants ADD COLUMN helmet_ok INTEGER NOT NULL DEFAULT 0")

    # start_number must become nullable — SQLite requires table recreation
    if col_info.get("start_number", {}).get("notnull", 0) == 1:
        # Drop dependent views first so SQLite doesn't complain during RENAME
        conn.execute("DROP VIEW IF EXISTS v_run_results")
        conn.execute("DROP VIEW IF EXISTS v_class_standings_sum_all")
        conn.execute("DROP VIEW IF EXISTS v_fastest_of_day")

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("DROP TABLE IF EXISTS Participants_v2")
        conn.execute("""
            CREATE TABLE Participants_v2 (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
                class_id        INTEGER REFERENCES Classes(id) ON DELETE SET NULL,
                club_id         INTEGER REFERENCES Clubs(id) ON DELETE SET NULL,
                start_number    INTEGER,
                first_name      TEXT    NOT NULL,
                last_name       TEXT    NOT NULL,
                birth_year      INTEGER,
                license_number  TEXT,
                status          TEXT    NOT NULL DEFAULT 'registered'
                                CHECK (status IN ('registered','checked_in','technical_ok','disqualified')),
                fee_paid        INTEGER NOT NULL DEFAULT 0 CHECK (fee_paid IN (0,1)),
                helmet_ok       INTEGER NOT NULL DEFAULT 0 CHECK (helmet_ok IN (0,1)),
                UNIQUE (event_id, start_number)
            )
        """)
        conn.execute("""
            INSERT INTO Participants_v2
            SELECT id, event_id, class_id, club_id,
                   NULLIF(start_number, 0),
                   first_name, last_name, birth_year, license_number, status,
                   COALESCE(fee_paid, 0), COALESCE(helmet_ok, 0)
            FROM Participants
        """)
        conn.execute("DROP TABLE Participants")
        conn.execute("ALTER TABLE Participants_v2 RENAME TO Participants")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_event ON Participants (event_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_start_number ON Participants (event_id, start_number)")
        conn.execute("PRAGMA foreign_keys = ON")


def _migrate_classes(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(Classes)")}
    if not existing:
        return  # fresh DB
    for col, ddl in [
        ("registration_closed_at", "ALTER TABLE Classes ADD COLUMN registration_closed_at TEXT"),
        ("start_time",             "ALTER TABLE Classes ADD COLUMN start_time TEXT"),
        ("end_time",               "ALTER TABLE Classes ADD COLUMN end_time TEXT"),
    ]:
        if col not in existing:
            conn.execute(ddl)


def _migrate_classes_exhibition(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(Classes)")}
    if not existing:
        return
    if "is_exhibition" not in existing:
        conn.execute("ALTER TABLE Classes ADD COLUMN is_exhibition INTEGER NOT NULL DEFAULT 0")


def _migrate_participants_unique_per_class(conn: sqlite3.Connection) -> None:
    """Change UNIQUE (event_id, start_number) → UNIQUE (class_id, start_number)."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='Participants'"
    ).fetchone()
    if not row:
        return  # fresh DB
    if "class_id, start_number" in row[0]:
        return  # already migrated

    for view in ("v_run_results", "v_class_standings_sum_all", "v_fastest_of_day"):
        conn.execute(f"DROP VIEW IF EXISTS {view}")

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TABLE IF EXISTS Participants_v3")
    conn.execute("""
        CREATE TABLE Participants_v3 (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
            class_id        INTEGER REFERENCES Classes(id) ON DELETE SET NULL,
            club_id         INTEGER REFERENCES Clubs(id) ON DELETE SET NULL,
            start_number    INTEGER,
            first_name      TEXT    NOT NULL,
            last_name       TEXT    NOT NULL,
            birth_year      INTEGER,
            license_number  TEXT,
            status          TEXT    NOT NULL DEFAULT 'registered'
                            CHECK (status IN ('registered','checked_in','technical_ok','disqualified')),
            fee_paid        INTEGER NOT NULL DEFAULT 0 CHECK (fee_paid IN (0,1)),
            helmet_ok       INTEGER NOT NULL DEFAULT 0 CHECK (helmet_ok IN (0,1)),
            UNIQUE (class_id, start_number)
        )
    """)
    conn.execute("INSERT INTO Participants_v3 SELECT * FROM Participants")
    conn.execute("DROP TABLE Participants")
    conn.execute("ALTER TABLE Participants_v3 RENAME TO Participants")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_event ON Participants (event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_participants_start_number ON Participants (class_id, start_number)")
    conn.execute("PRAGMA foreign_keys = ON")


def _migrate_classes_status(conn: sqlite3.Connection) -> None:
    """Add 'paused' to run_status CHECK constraint via table recreation."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='Classes'"
    ).fetchone()
    if not row:
        return  # fresh DB — executescript will create with correct CHECK
    if "'paused'" in row[0]:
        return  # already up to date

    for view in ("v_run_results", "v_class_standings_sum_all", "v_fastest_of_day"):
        conn.execute(f"DROP VIEW IF EXISTS {view}")

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TABLE IF EXISTS Classes_v2")
    conn.execute("""
        CREATE TABLE Classes_v2 (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id                 INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
            reglement_id             INTEGER REFERENCES Reglements(id) ON DELETE SET NULL,
            name                     TEXT    NOT NULL,
            short_name               TEXT,
            min_birth_year           INTEGER,
            max_birth_year           INTEGER,
            run_status               TEXT    NOT NULL DEFAULT 'planned'
                                     CHECK (run_status IN ('planned','running','paused','preliminary','official')),
            start_order              INTEGER NOT NULL DEFAULT 0,
            registration_closed_at   TEXT,
            start_time               TEXT,
            end_time                 TEXT,
            UNIQUE (event_id, name)
        )
    """)
    conn.execute("""
        INSERT INTO Classes_v2
        SELECT id, event_id, reglement_id, name, short_name,
               min_birth_year, max_birth_year, run_status,
               start_order, registration_closed_at, start_time, end_time
        FROM Classes
    """)
    conn.execute("DROP TABLE Classes")
    conn.execute("ALTER TABLE Classes_v2 RENAME TO Classes")
    conn.execute("PRAGMA foreign_keys = ON")
