"""File-backed local memory; no database dependency."""
import json
import os
from pathlib import Path
import tempfile
from threading import RLock


class LocalMemory:
    def __init__(self, path='aicourt-memory.json'):
        self.path = Path(path)
        self.lock = RLock()
        if self.path.suffix in {'.db', '.sqlite', '.sqlite3'}:
            raise ValueError('Use a JSON path; existing SQLite files are not modified')
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}
        if not isinstance(self.data, dict):
            raise ValueError('Memory must contain a JSON object')

    def put(self, key, value):
        with self.lock:
            updated = {**self.data, key: value}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=self.path.parent, prefix='.memory-')
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(updated, f, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(name, self.path)
                self.data = updated
            finally:
                if os.path.exists(name):
                    os.unlink(name)

    def get(self, key):
        with self.lock:
            return self.data.get(key)
