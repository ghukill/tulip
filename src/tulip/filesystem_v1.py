"""src/tulip/filesystem.py"""

import json
from itertools import accumulate
from pathlib import Path
from typing import BinaryIO

from fs import open_fs
from fs.base import FS

from .objects import TulipFile, TulipObject


class TulipFS(FS):
    """A PyFilesystem compliant filesystem built on top of dual PyFilesystem instances.

    This filesystem ensures that all operations on objects are mirrored with
    appropriate metadata operations in the assets filesystem.
    """

    def __init__(self, objects_fs: str | FS, assets_fs: str | FS):
        super().__init__()
        self.objects_fs = self._load_fs(objects_fs)
        self.assets_fs = self._load_fs(assets_fs)

    def _load_fs(self, _fs: str | FS) -> FS:
        match _fs:
            case str():
                return open_fs(_fs)
            case FS():
                return _fs
            case _:
                raise ValueError("A PyFilesystem instance or URI required")

    def write_metadata(self, path: str, metadata: dict) -> bool:
        """Write TulipObject or TulipFile metadata to assets filesystem."""
        self.assets_fs.makedirs(path, recreate=True)
        self.assets_fs.writebytes(
            str(Path(path) / "tulip.json"),
            json.dumps(metadata).encode(),
        )
        return True

    # -----------------------------------------------------------------------
    # Write/Update Metadata Methods
    # -----------------------------------------------------------------------

    def makedir(self, path, permissions=None, recreate=False):
        result = self.objects_fs.makedir(path, permissions=permissions, recreate=recreate)

        try:
            tulip_object = TulipObject(path)
            metadata = tulip_object.generate_metadata()
            self.write_metadata(path, metadata)
        except Exception as e:
            try:
                self.objects_fs.removedir(path)
            except Exception:
                pass
            raise e

        return result

    def makedirs(self, path, permissions=None, recreate=False):
        result = self.objects_fs.makedirs(
            str(path),
            permissions=permissions,
            recreate=True,
        )

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
                self.objects_fs.removetree(path)
            except Exception:
                pass
            raise e

        return result

    def writebytes(self, path, contents):
        result = self.objects_fs.writebytes(path, contents)

        try:
            tulip_file = TulipFile(path, contents)
            metadata = tulip_file.generate_metadata()
            self.write_metadata(path, metadata)
        except Exception as e:
            try:
                self.objects_fs.remove(path)
            except Exception:
                pass
            raise e

        return result

    def openbin(self, path, mode="r", buffering=-1, **options):
        file_handle = self.objects_fs.openbin(path, mode, buffering, **options)

        if any(m in mode for m in ["w", "a", "+"]):
            return TulipFileHandle(file_handle, self, path, mode)
        else:
            return file_handle

    # -----------------------------------------------------------------------
    # Delete Metadata Methods
    # -----------------------------------------------------------------------

    def removedir(self, path):
        metadata_existed = self.assets_fs.exists(path)

        try:
            self.assets_fs.removetree(path)
        except Exception as e:
            if metadata_existed:
                raise e

        result = self.objects_fs.removedir(path)
        return result

    def removetree(self, dir_path: str) -> None:
        metadata_existed = self.assets_fs.exists(dir_path)

        try:
            self.assets_fs.removetree(dir_path)
        except Exception as e:
            if metadata_existed:
                raise e

        result = self.objects_fs.removetree(dir_path)
        return result

    def remove(self, path):
        metadata_existed = self.assets_fs.exists(path)

        try:
            self.assets_fs.removetree(path)
        except Exception as e:
            if metadata_existed:
                raise e

        result = self.objects_fs.remove(path)
        return result

    # ------------------------------------------------------------------------
    # Delegated Methods
    # ------------------------------------------------------------------------

    def writetext(
        self,
        path: str,
        contents: str,
        encoding: str = "utf-8",
        errors=None,
        newline: str = "",
    ):
        encoded_contents = contents.encode(encoding)
        return self.writebytes(path, encoded_contents)

    def readbytes(self, path):
        return self.objects_fs.readbytes(path)

    def readtext(
        self,
        path,
        encoding=None,
        errors=None,
        newline="",
    ):
        return self.objects_fs.readtext(
            path,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

    def exists(self, path):
        return self.objects_fs.exists(path)

    def setinfo(self, path, info):
        return self.objects_fs.setinfo(path, info)

    def getinfo(self, path, namespaces=None):
        return self.objects_fs.getinfo(path, namespaces)

    def isfile(self, path):
        return self.objects_fs.isfile(path)

    def isdir(self, path):
        return self.objects_fs.isdir(path)

    def listdir(self, path):
        return self.objects_fs.listdir(path)


class TulipFileHandle:
    """Wrapper around file handle that generates metadata on close.

    Example use: TulipFS.openbin().  This returns a file like object, which on creation or
    update, we'll want to update the associated assets metadata.
    """

    def __init__(self, file_handle: BinaryIO, tulip_fs: "TulipFS", path: str, mode: str):
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
                contents = self._tulip_fs.objects_fs.readbytes(self._path)
                tulip_file = TulipFile(self._path, contents)
                metadata = tulip_file.generate_metadata()
                self._tulip_fs.write_metadata(self._path, metadata)
            except Exception as e:
                try:
                    self._tulip_fs.objects_fs.remove(self._path)
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
