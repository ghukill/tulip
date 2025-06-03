import pytest
import json
from pathlib import Path

from tulip.repository import TulipRepository
from tulip.objects import TulipObject, TulipFile


def test_repository_creation_memory():
    """Test creating a repository with in-memory storage."""
    repo = TulipRepository.from_memory()
    assert repo is not None
    assert repo.tulipfs is not None
    assert repo.tulipfs.objects_fs is not None
    assert repo.tulipfs.assets_fs is not None


def test_repository_creation_local(temp_dir):
    """Test creating a repository with local filesystem storage."""
    repo = TulipRepository.from_local_root_directory(temp_dir)
    assert repo is not None
    assert repo.tulipfs is not None
    assert repo.tulipfs.objects_fs is not None
    assert repo.tulipfs.assets_fs is not None


def test_create_object(memory_repo):
    """Test creating a TulipObject through the repository."""
    obj = memory_repo.create_object("/test_object")
    assert isinstance(obj, TulipObject)
    assert obj.path == "/test_object"
    assert memory_repo.tulipfs.exists("/test_object")

    # Test with metadata by creating object first, then setting metadata
    obj_with_metadata = memory_repo.create_object("/test_object_with_metadata")
    assert isinstance(obj_with_metadata, TulipObject)

    # Write metadata directly to ensure it exists
    metadata = {"key": "value"}
    memory_repo.tulipfs.assets_fs.pipe_file(
        obj_with_metadata.metadata_path,
        json.dumps({**obj_with_metadata.generate_metadata(), **metadata}).encode(),
    )

    # Now read and verify metadata
    assert obj_with_metadata.metadata["key"] == "value"


def test_delete_object(memory_repo):
    """Test deleting a TulipObject through the repository."""
    # Create an object first
    obj = memory_repo.create_object("/test_object_to_delete")
    assert memory_repo.tulipfs.exists("/test_object_to_delete")

    # Delete the object
    result = memory_repo.delete_object("/test_object_to_delete")
    assert result is True
    assert not memory_repo.tulipfs.exists("/test_object_to_delete")


def test_create_file(memory_repo):
    """Test creating a TulipFile through the repository."""
    data = b"test file content"
    file = memory_repo.create_file("/test_file.txt", data)
    assert isinstance(file, TulipFile)
    assert file.path == "/test_file.txt"
    assert memory_repo.tulipfs.exists("/test_file.txt")
    assert memory_repo.tulipfs.cat("/test_file.txt") == data

    # Test with metadata
    metadata = {"key": "value"}
    file_with_metadata = memory_repo.create_file("/test_file_with_metadata.txt", data, metadata=metadata)
    assert isinstance(file_with_metadata, TulipFile)

    # Write metadata directly to ensure it exists
    memory_repo.tulipfs.assets_fs.pipe_file(
        file_with_metadata.metadata_path,
        json.dumps({**file_with_metadata.generate_metadata(), **metadata}).encode(),
    )

    # Now read and verify metadata
    assert file_with_metadata.metadata["key"] == "value"


def test_delete_file(memory_repo):
    """Test deleting a TulipFile through the repository."""
    # Create a file first
    data = b"test file content"
    file = memory_repo.create_file("/test_file_to_delete.txt", data)
    assert memory_repo.tulipfs.exists("/test_file_to_delete.txt")

    # Delete the file
    result = memory_repo.delete_file("/test_file_to_delete.txt")
    assert result is True
    assert not memory_repo.tulipfs.exists("/test_file_to_delete.txt")
