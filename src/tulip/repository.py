"""src/tulip/repository.py"""

import json
from pathlib import Path

import fsspec
from fsspec.spec import AbstractFileSystem
from fsspec.implementations.dirfs import DirFileSystem

from .filesystem import TulipFS
from .objects import TulipFile, TulipObject


class TulipRepository:
    def __init__(self, objects_fs: AbstractFileSystem, assets_fs: AbstractFileSystem):
        self.tulipfs = TulipFS(objects_fs=objects_fs, assets_fs=assets_fs)

    @classmethod
    def from_local_root_directory(cls, root_path: str | Path = "/tmp/tulip"):
        objects_fs = DirFileSystem(
            str(Path(root_path) / "objects"), fsspec.filesystem("file")
        )
        assets_fs = DirFileSystem(
            str(Path(root_path) / "assets"), fsspec.filesystem("file")
        )
        for fs in [objects_fs, assets_fs]:
            if not fs.exists("/"):
                fs.makedirs("/")
        return cls(objects_fs=objects_fs, assets_fs=assets_fs)

    @classmethod
    def from_memory(cls):
        objects_fs = DirFileSystem("/tmp/tulip/objects", fsspec.filesystem("memory"))
        assets_fs = DirFileSystem("/tmp/tulip/assets", fsspec.filesystem("memory"))
        for fs in [objects_fs, assets_fs]:
            if not fs.exists("/"):
                fs.makedirs("/")
        return cls(objects_fs=objects_fs, assets_fs=assets_fs)

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
