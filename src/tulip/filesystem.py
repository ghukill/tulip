"""src/tulip/filesystem.py"""

from itertools import accumulate
import json
from pathlib import Path
from typing import BinaryIO

import fsspec
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.spec import AbstractFileSystem

from .objects import TulipFile, TulipObject


class TulipFS(AbstractFileSystem):
    protocol = "tulip"
    sep = "/"
    root_marker = "/"

    def __init__(
        self,
        objects_fs: str | AbstractFileSystem,
        assets_fs: str | AbstractFileSystem,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(objects_fs, str):
            self.objects_fs = fsspec.filesystem(
                objects_fs.split("://")[0], **self._parse_fs_url(objects_fs)
            )
        else:
            self.objects_fs = objects_fs
        if isinstance(assets_fs, str):
            self.assets_fs = fsspec.filesystem(
                assets_fs.split("://")[0], **self._parse_fs_url(assets_fs)
            )
        else:
            self.assets_fs = assets_fs

        # TODO: fix this wrap
        self.objects_fs = DirFileSystem("/tmp/tulip/objects", self.objects_fs)
        self.assets_fs = DirFileSystem("/tmp/tulip/assets", self.assets_fs)

    def _parse_fs_url(self, url: str) -> dict:
        """Parse filesystem URL into protocol and options."""
        protocol, path = url.split("://", 1)
        print(path)
        if protocol == "file":
            return {"path": path}
        # TODO: support more methods here
        else:
            raise ValueError(f"Filesystem protocol not supported: '{protocol}'")

    def write_metadata(self, path: str, metadata: dict) -> bool:
        """Write TulipObject or TulipFile metadata to assets filesystem."""
        self.assets_fs.makedirs(path, exist_ok=True)
        metadata_path = str(Path(path) / "tulip.json")
        with self.assets_fs.open(metadata_path, "wb") as f:
            f.write(json.dumps(metadata).encode())
        return True

    # -----------------------------------------------------------------------
    # Write/Update Metadata Methods
    # -----------------------------------------------------------------------

    def makedir(self, path, create_parents=False, **kwargs):
        """Create a single directory and generate metadata."""
        # Create directory in objects filesystem
        self.objects_fs.makedirs(path, exist_ok=False)

        try:
            tulip_object = TulipObject(path)
            metadata = tulip_object.generate_metadata()
            self.write_metadata(path, metadata)
        except Exception as e:
            try:
                self.objects_fs.rmdir(path)
            except Exception:
                pass
            raise e

        return True

    def makedirs(self, path, exist_ok=False):
        """Create directories recursively and generate metadata for each."""
        # Create all directories in objects filesystem
        self.objects_fs.makedirs(path, exist_ok=exist_ok)

        created_paths = []
        try:
            path_obj = Path(path.removeprefix("/"))
            for current_path in accumulate(path_obj.parts, lambda a, b: str(Path(a) / b)):
                tulip_object = TulipObject(current_path)
                metadata = tulip_object.generate_metadata()
                self.write_metadata(current_path, metadata)
                created_paths.append(current_path)
        except Exception as e:
            try:
                self.objects_fs.rm(path, recursive=True)
            except Exception:
                pass
            raise e

        return True

    def pipe_file(self, path, value, mode="overwrite", **kwargs):
        """Write bytes to a file and generate metadata."""
        with self.objects_fs.open(path, "wb") as f:
            f.write(value)

        try:
            tulip_file = TulipFile(path, value)
            metadata = tulip_file.generate_metadata()
            self.write_metadata(path, metadata)
        except Exception as e:
            try:
                self.objects_fs.rm(path)
            except Exception:
                pass
            raise e

        return True

    def _open(self, path, mode="rb", **kwargs):
        """Open a file, wrapping write modes to generate metadata on close."""
        file_handle = self.objects_fs.open(path, mode, **kwargs)

        if any(m in mode for m in ["w", "a", "+"]):
            return TulipFileHandle(file_handle, self, path, mode)
        else:
            return file_handle

    # -----------------------------------------------------------------------
    # Delete Metadata Methods
    # -----------------------------------------------------------------------

    def rmdir(self, path):
        """Remove a directory and its metadata."""
        metadata_existed = self.assets_fs.exists(path)

        try:
            self.assets_fs.rm(path, recursive=True)
        except Exception as e:
            if metadata_existed:
                raise e

        result = self.objects_fs.rmdir(path)
        return result

    def rm(self, path, recursive=False, maxdepth=None):
        """Remove file(s) or directory and associated metadata."""
        metadata_existed = self.assets_fs.exists(path)

        try:
            self.assets_fs.rm(
                path, recursive=True
            )  # Always recursive for metadata cleanup
        except Exception as e:
            if metadata_existed:
                raise e

        result = self.objects_fs.rm(path, recursive=recursive, maxdepth=maxdepth)
        return result

    # ------------------------------------------------------------------------
    # Delegated Methods
    # ------------------------------------------------------------------------

    def cat_file(self, path, **kwargs):
        """Read entire file as bytes."""
        return self.objects_fs.cat_file(path, **kwargs)

    def cat(self, path, **kwargs):
        """Read file(s) as bytes."""
        return self.objects_fs.cat(path, **kwargs)

    def exists(self, path, **kwargs):
        """Check if path exists."""
        return self.objects_fs.exists(path, **kwargs)

    def info(self, path, **kwargs):
        """Get file/directory info."""
        return self.objects_fs.info(path, **kwargs)

    def isfile(self, path):
        """Check if path is a file."""
        return self.objects_fs.isfile(path)

    def isdir(self, path):
        """Check if path is a directory."""
        return self.objects_fs.isdir(path)

    def ls(self, path="", detail=True, **kwargs):
        """List directory contents."""
        return self.objects_fs.ls(path, detail=detail, **kwargs)

    def listdir(self, path=""):
        """List directory contents (names only)."""
        return [
            item["name"] if isinstance(item, dict) else item
            for item in self.ls(path, detail=False)
        ]

    def glob(self, path, **kwargs):
        """Find files by glob pattern."""
        return self.objects_fs.glob(path, **kwargs)

    def find(self, path, **kwargs):
        """Find files recursively."""
        return self.objects_fs.find(path, **kwargs)

    def size(self, path):
        """Get file size."""
        return self.objects_fs.size(path)

    def checksum(self, path):
        """Get file checksum."""
        return self.objects_fs.checksum(path)

    def copy(self, path1, path2, **kwargs):
        """Copy file and metadata."""
        # Copy in objects filesystem
        result = self.objects_fs.copy(path1, path2, **kwargs)

        # Copy metadata if it exists
        if self.assets_fs.exists(path1):
            self.assets_fs.copy(path1, path2, recursive=True, **kwargs)

        return result

    def move(self, path1, path2, **kwargs):
        """Move file and metadata."""
        # Move in objects filesystem
        result = self.objects_fs.move(path1, path2, **kwargs)

        # Move metadata if it exists
        if self.assets_fs.exists(path1):
            self.assets_fs.move(path1, path2, **kwargs)

        return result


class TulipFileHandle:
    """Wrapper around file handle that generates metadata on close."""

    def __init__(self, file_handle: BinaryIO, tulip_fs: TulipFS, path: str, mode: str):
        self._handle = file_handle
        self._tulip_fs = tulip_fs
        self._path = path
        self._mode = mode
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the file and generate metadata if it was written to."""
        if not self._closed:
            self._handle.close()
            self._closed = True

            if any(m in self._mode for m in ["w", "a", "+"]):
                self._generate_metadata()

    def _generate_metadata(self):
        if self._tulip_fs.objects_fs.exists(self._path):
            try:
                contents = self._tulip_fs.objects_fs.cat_file(self._path)
                tulip_file = TulipFile(self._path, contents)
                metadata = tulip_file.generate_metadata()
                self._tulip_fs.write_metadata(self._path, metadata)
            except Exception as e:
                try:
                    self._tulip_fs.objects_fs.rm(self._path)
                except Exception:
                    pass
                raise e

    def write(self, data):
        return self._handle.write(data)

    def read(self, size=-1):
        return self._handle.read(size)

    def readline(self, size=-1):
        return self._handle.readline(size)

    def readlines(self, hint=-1):
        return self._handle.readlines(hint)

    def seek(self, offset, whence=0):
        return self._handle.seek(offset, whence)

    def tell(self):
        return self._handle.tell()

    def flush(self):
        return self._handle.flush()

    def fileno(self):
        return self._handle.fileno()

    def isatty(self):
        return self._handle.isatty()

    def readable(self):
        return self._handle.readable()

    def writable(self):
        return self._handle.writable()

    def seekable(self):
        return self._handle.seekable()

    def __getattr__(self, name):
        return getattr(self._handle, name)
