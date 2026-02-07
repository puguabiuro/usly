import sqlite3

DB_PATH = "usly.db"

COLUMNS = [
    ("pricing_type", "TEXT NOT NULL DEFAULT 'free'"),
    ("price_fixed", "INTEGER"),
    ("price_min", "INTEGER"),
    ("price_max", "INTEGER"),
    ("payment_link", "TEXT"),
]

def main():
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.cursor()

        # upewnij się, że tabela events istnieje
        tables = [
            r[0]
            for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
            ).fetchall()
        ]
        if "events" not in tables:
            raise SystemExit("Tabela 'events' nie istnieje w bazie.")

        # istniejące kolumny
        existing_cols = {
            r[1] for r in cur.execute("PRAGMA table_info(events)").fetchall()
        }

        for name, ddl in COLUMNS:
            if name in existing_cols:
                print(f"OK: kolumna już istnieje: {name}")
                continue
            sql = f"ALTER TABLE events ADD COLUMN {name} {ddl};"
            print(f"DODAJĘ: {sql}")
            cur.execute(sql)

        con.commit()

        # kontrola
        cols_after = [
            r[1] for r in cur.execute("PRAGMA table_info(events)").fetchall()
        ]
        print("KOLUMNY events:", cols_after)
        print("MIGRACJA OK")
    finally:
        con.close()

if __name__ == "__main__":
    main()
