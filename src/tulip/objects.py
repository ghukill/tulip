"""src/tulip/objects.py"""

import json

import hashlib
from abc import abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .repository import TulipRepository


class TulipEntity:
    def __init__(
        self,
        path: str,
        metadata_mixins: dict | None = None,
        repository: Optional["TulipRepository"] = None,
    ):
        self.path = path
        self.metadata_mixins = metadata_mixins
        self.repository = repository

    @property
    def metadata(self) -> dict:
        return self.read_metadata()

    @property
    def metadata_path(self):
        return str(Path(self.path) / "tulip.json")

    @abstractmethod
    def generate_metadata(self) -> dict: ...

    @abstractmethod
    def save(self): ...

    @abstractmethod
    def delete(self): ...

    def read_metadata(self):
        return json.loads(self.repository.tulipfs.assets_fs.cat(self.metadata_path))

    def update_metadata(self, metadata_mixins: dict):
        metadata = self.read_metadata()
        metadata.update(metadata_mixins)
        self.repository.tulipfs.assets_fs.pipe_file(
            self.metadata_path,
            json.dumps(metadata).encode(),
        )


class TulipObject(TulipEntity):
    def generate_metadata(self) -> dict:
        return {
            "type": "object",
            "path": self.path,
            "name": Path(self.path).name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self):
        tulipfs_result = self.repository.tulipfs.makedirs(self.path)
        if self.metadata_mixins is not None:
            self.update_metadata(self.metadata_mixins)
        return tulipfs_result

    def delete(self, recursive=True):
        if recursive:
            return self.repository.tulipfs.rm(self.path, recursive=True)
        else:
            return self.repository.tulipfs.rmdir(self.path)


class TulipFile(TulipEntity):
    def __init__(
        self,
        path: str,
        data: bytes = None,
        metadata_mixins: dict | None = None,
        repository: Optional["TulipRepository"] = None,
    ):
        super().__init__(path, metadata_mixins=metadata_mixins, repository=repository)
        self.data = data

    def generate_metadata(self) -> dict:
        return {
            "type": "file",
            "path": self.path,
            "name": Path(self.path).name,
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

    def save(self):
        tulipfs_result = self.repository.tulipfs.pipe_file(self.path, self.data)
        if self.metadata_mixins is not None:
            self.update_metadata(self.metadata_mixins)
        return tulipfs_result

    def delete(self) -> dict:
        return self.repository.tulipfs.rm(self.path)
