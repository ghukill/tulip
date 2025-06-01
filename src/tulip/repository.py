"""src/tulip/repository.py"""

import json
from pathlib import Path

from fs import open_fs

from .filesystem import TulipFS
from .objects import TulipFile, TulipObject


class TulipRepository:
    def __init__(self, object_fs: str, asset_fs: str):
        self.tulipfs = TulipFS(
            open_fs(object_fs),
            open_fs(asset_fs),
        )

    @classmethod
    def from_local_root_path(cls, root_path: Path | str) -> "TulipRepository":
        """Init a TulipRepository from a single root on the local filesystem."""
        root_path = Path(root_path)
        object_fs = root_path / "objects"
        asset_fs = root_path / "assets"

        object_fs.mkdir(parents=True, exist_ok=True)
        asset_fs.mkdir(parents=True, exist_ok=True)

        return cls(str(object_fs), str(asset_fs))

    @classmethod
    def from_filesystems(cls, object_fs: str, asset_fs: str) -> "TulipRepository":
        """Init a TulipRepository from two explicit PyFilesystems."""
        return cls(object_fs, asset_fs)

    @classmethod
    def from_memory(cls):
        """Init a TulipRepository with both filesystems in memory."""
        return cls(object_fs="mem://", asset_fs="mem://")

    @classmethod
    def from_config(cls, config_path: str | Path):
        """Init a TulipRepository from a configuration file."""
        with open(config_path) as f:
            config = json.load(f)
        return cls(object_fs=config["object_fs"], asset_fs=config["asset_fs"])

    def create_object(
        self, path: str | Path, metadata: dict | None = None
    ) -> TulipObject:
        tulip_object = TulipObject(path, metadata_mixins=metadata, repository=self)
        tulip_object.save()
        return tulip_object

    def delete_object(self, path: str | Path, recursive=False):
        tulip_object = TulipObject(path, repository=self)
        tulip_object.delete(recursive=recursive)
        return True

    def create_file(
        self, path: str | Path, data: bytes, metadata: dict | None = None
    ) -> TulipFile:
        tulip_file = TulipFile(path, data, metadata_mixins=metadata, repository=self)
        tulip_file.save()
        return tulip_file

    def delete_file(self, path: str | Path):
        tulip_file = TulipFile(path, repository=self)
        tulip_file.delete()
        return True
