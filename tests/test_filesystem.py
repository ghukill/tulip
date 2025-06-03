import pytest
from pathlib import Path

from tulip.filesystem import TulipFS


def test_tulipfs_initialization(memory_repo):
    """Test initializing a TulipFS instance."""
    tulipfs = memory_repo.tulipfs
    assert isinstance(tulipfs, TulipFS)
    assert tulipfs.objects_fs is not None
    assert tulipfs.assets_fs is not None


def test_makedir(memory_repo):
    """Test creating a directory."""
    tulipfs = memory_repo.tulipfs
    path = "/test_dir"

    # Create directory
    result = tulipfs.makedir(path)
    assert result is True
    assert tulipfs.exists(path)
    assert tulipfs.isdir(path)

    # Check metadata exists
    assert tulipfs.assets_fs.exists(f"{path}/tulip.json")


def test_makedirs(memory_repo):
    """Test creating directories recursively."""
    tulipfs = memory_repo.tulipfs
    path = "/parent/child/grandchild"

    # Create directories
    result = tulipfs.makedirs(path)
    assert result is True

    # Check that all directories in the path exist
    assert tulipfs.exists(path)
    assert tulipfs.isdir(path)
    assert tulipfs.exists("/parent")
    assert tulipfs.isdir("/parent")
    assert tulipfs.exists("/parent/child")
    assert tulipfs.isdir("/parent/child")


def test_pipe_file(memory_repo):
    """Test writing data to a file."""
    tulipfs = memory_repo.tulipfs
    path = "/test_file.txt"
    data = b"test file content"

    # Write file
    result = tulipfs.pipe_file(path, data)
    assert result is True
    assert tulipfs.exists(path)
    assert tulipfs.isfile(path)

    # Check file content
    assert tulipfs.cat(path) == data

    # Check metadata exists
    assert tulipfs.assets_fs.exists(f"{path}/tulip.json")


def test_open_read(memory_repo):
    """Test opening a file for reading."""
    tulipfs = memory_repo.tulipfs
    path = "/test_file_open.txt"
    data = b"test file content for open"

    # Create file first
    tulipfs.pipe_file(path, data)

    # Open and read file
    with tulipfs.open(path, "rb") as f:
        content = f.read()

    assert content == data


def test_open_write(memory_repo):
    """Test opening a file for writing."""
    tulipfs = memory_repo.tulipfs
    path = "/test_file_write.txt"
    data = b"test file content for write"

    # Open and write file
    with tulipfs.open(path, "wb") as f:
        f.write(data)

    # Check file content
    assert tulipfs.exists(path)
    assert tulipfs.cat(path) == data

    # Check metadata exists
    assert tulipfs.assets_fs.exists(f"{path}/tulip.json")


def test_rm_file(memory_repo):
    """Test removing a file."""
    tulipfs = memory_repo.tulipfs
    path = "/test_file_rm.txt"
    data = b"test file content for rm"

    # Create file first
    tulipfs.pipe_file(path, data)
    assert tulipfs.exists(path)

    # Remove file
    tulipfs.rm(path)
    assert not tulipfs.exists(path)
    assert not tulipfs.assets_fs.exists(f"{path}/tulip.json")


def test_rm_dir_recursive(memory_repo):
    """Test removing a directory recursively."""
    tulipfs = memory_repo.tulipfs
    parent_path = "/parent_rm"
    child_path = f"{parent_path}/child_rm"
    file_path = f"{child_path}/file.txt"

    # Create directory structure
    tulipfs.makedirs(child_path)
    tulipfs.pipe_file(file_path, b"test content")

    # Remove parent directory recursively
    tulipfs.rm(parent_path, recursive=True)
    assert not tulipfs.exists(parent_path)
    assert not tulipfs.exists(child_path)
    assert not tulipfs.exists(file_path)
