"""src/tulip/repository.py"""

from pathlib import Path

from fs import open_fs

from .filesystem import TulipFS


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
