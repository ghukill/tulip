"""src/tulip/objects.py"""

import hashlib
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from fs.path import basename


class TulipEntity:
    def __init__(self, path: str):
        self.path = path

    @property
    def metadata_path(self):
        return str(Path(self.path) / "tulip.json")

    @abstractmethod
    def get_metadata(self) -> dict: ...


class TulipObject(TulipEntity):
    def get_metadata(self) -> dict:
        return {
            "type": "object",
            "path": self.path,
            "name": basename(self.path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


class TulipFile(TulipEntity):
    def __init__(self, path: str, data: bytes = None):
        super().__init__(path)
        self.data = data

    def get_metadata(self) -> dict:
        return {
            "type": "file",
            "path": self.path,
            "name": basename(self.path),
            "size": self._get_file_size(),
            "digests": self._get_digests(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_file_size(self) -> int:
        if self.data is not None:
            return len(self.data)
        return 0

    def _get_digests(self) -> dict:
        if self.data is not None:
            sha256_hash = hashlib.sha256(self.data).hexdigest()
            return {"sha256": sha256_hash}
        return {"sha256": None}
