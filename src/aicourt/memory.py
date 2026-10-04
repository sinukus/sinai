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

    def get(self, key, default=None):
        with self.lock:
            return self.data.get(key, default)

    def snapshot(self):
        """Return a detached copy suitable for prompt/context assembly."""
        with self.lock:
            return json.loads(json.dumps(self.data, ensure_ascii=False))

    def append(self, key, value, limit=None):
        """Atomically append to a local list, optionally retaining only the newest items."""
        with self.lock:
            items = list(self.data.get(key) or [])
            items.append(value)
            if limit is not None:
                if limit < 1:
                    raise ValueError('limit must be positive')
                items = items[-limit:]
            self.put(key, items)
            return list(items)

    def forget(self, key):
        """Remove one local-memory key without touching unrelated state."""
        with self.lock:
            if key not in self.data:
                return False
            updated = dict(self.data)
            del updated[key]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(dir=self.path.parent, prefix='.memory-')
            try:
                with os.fdopen(fd, 'w') as out:
                    json.dump(updated, out, ensure_ascii=False)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(name, self.path)
                self.data = updated
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            return True
