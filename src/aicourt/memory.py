import sqlite3


class LocalMemory:
    def __init__(self, path="aicourt.db"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS memory(key TEXT PRIMARY KEY,value TEXT)"
        )

    def put(self, key, value):
        statement = (
            "INSERT INTO memory VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        )
        self.db.execute(statement, (key, value))
        self.db.commit()

    def get(self, key):
        row = self.db.execute(
            "SELECT value FROM memory WHERE key=?", (key,)
        ).fetchone()
        return row[0] if row else None
