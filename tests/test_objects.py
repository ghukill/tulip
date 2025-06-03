import pytest
import json
from pathlib import Path

from tulip.objects import TulipObject, TulipFile


def test_tulip_object_creation(memory_repo):
    """Test creating a TulipObject."""
    path = "/test_object"
    obj = TulipObject(path, repository=memory_repo)

    assert obj.path == path
    assert obj.repository == memory_repo
    assert obj.metadata_mixins is None


def test_tulip_object_with_metadata(memory_repo):
    """Test creating a TulipObject with metadata."""
    path = "/test_object_metadata"
    metadata = {"key": "value", "another_key": 123}
    obj = TulipObject(path, metadata_mixins=metadata, repository=memory_repo)

    assert obj.path == path
    assert obj.repository == memory_repo
    assert obj.metadata_mixins == metadata


def test_tulip_object_generate_metadata(memory_repo):
    """Test generating metadata for a TulipObject."""
    path = "/test_object_gen_metadata"
    obj = TulipObject(path, repository=memory_repo)

    metadata = obj.generate_metadata()

    assert metadata["type"] == "object"
    assert metadata["path"] == path
    assert metadata["name"] == "test_object_gen_metadata"
    assert "created_at" in metadata
    assert "updated_at" in metadata


def test_tulip_object_save_and_read_metadata(memory_repo):
    """Test saving a TulipObject and reading its metadata."""
    path = "/test_object_save"
    obj = TulipObject(path, repository=memory_repo)

    # Save the object
    obj.save()

    # Check that the object exists
    assert memory_repo.tulipfs.exists(path)

    # Add metadata after saving
    metadata_mixins = {"custom_key": "custom_value"}
    # Write metadata directly to avoid reading it first
    memory_repo.tulipfs.assets_fs.pipe_file(
        obj.metadata_path,
        json.dumps({**obj.generate_metadata(), **metadata_mixins}).encode(),
    )

    # Read metadata
    metadata = obj.metadata

    assert metadata["type"] == "object"
    assert metadata["path"] == path
    assert metadata["custom_key"] == "custom_value"


def test_tulip_object_update_metadata(memory_repo):
    """Test updating metadata for a TulipObject."""
    path = "/test_object_update"
    obj = TulipObject(path, repository=memory_repo)

    # Save the object
    obj.save()

    # Write initial metadata
    memory_repo.tulipfs.assets_fs.pipe_file(
        obj.metadata_path,
        json.dumps(obj.generate_metadata()).encode(),
    )

    # Update metadata
    update_data = {"new_key": "new_value"}
    obj.update_metadata(update_data)

    # Read metadata
    metadata = obj.metadata

    assert metadata["new_key"] == "new_value"


def test_tulip_object_delete(memory_repo):
    """Test deleting a TulipObject."""
    path = "/test_object_delete"
    obj = TulipObject(path, repository=memory_repo)

    # Save the object
    obj.save()
    assert memory_repo.tulipfs.exists(path)

    # Delete the object
    obj.delete()
    assert not memory_repo.tulipfs.exists(path)


def test_tulip_file_creation(memory_repo):
    """Test creating a TulipFile."""
    path = "/test_file.txt"
    data = b"test file content"
    file = TulipFile(path, data, repository=memory_repo)

    assert file.path == path
    assert file.data == data
    assert file.repository == memory_repo
    assert file.metadata_mixins is None


def test_tulip_file_with_metadata(memory_repo):
    """Test creating a TulipFile with metadata."""
    path = "/test_file_metadata.txt"
    data = b"test file content"
    metadata = {"key": "value", "another_key": 123}
    file = TulipFile(path, data, metadata_mixins=metadata, repository=memory_repo)

    assert file.path == path
    assert file.data == data
    assert file.repository == memory_repo
    assert file.metadata_mixins == metadata


def test_tulip_file_generate_metadata(memory_repo):
    """Test generating metadata for a TulipFile."""
    path = "/test_file_gen_metadata.txt"
    data = b"test file content for metadata generation"
    file = TulipFile(path, data, repository=memory_repo)

    metadata = file.generate_metadata()

    assert metadata["type"] == "file"
    assert metadata["path"] == path
    assert metadata["name"] == "test_file_gen_metadata.txt"
    assert metadata["size"] == len(data)
    assert "digests" in metadata
    assert "sha256" in metadata["digests"]
    assert "created_at" in metadata
    assert "updated_at" in metadata


def test_tulip_file_save_and_read(memory_repo):
    """Test saving a TulipFile and reading its content."""
    path = "/test_file_save.txt"
    data = b"test file content for save and read"
    metadata_mixins = {"custom_key": "custom_value"}
    file = TulipFile(path, data, metadata_mixins=metadata_mixins, repository=memory_repo)

    # Save the file
    file.save()

    # Check that the file exists
    assert memory_repo.tulipfs.exists(path)

    # Read file content
    content = memory_repo.tulipfs.cat(path)
    assert content == data

    # Read metadata
    metadata = file.metadata

    assert metadata["type"] == "file"
    assert metadata["path"] == path
    assert metadata["size"] == len(data)
    assert metadata["custom_key"] == "custom_value"


def test_tulip_file_update_metadata(memory_repo):
    """Test updating metadata for a TulipFile."""
    path = "/test_file_update.txt"
    data = b"test file content for update"
    file = TulipFile(path, data, repository=memory_repo)

    # Save the file
    file.save()

    # Update metadata
    update_data = {"new_key": "new_value"}
    file.update_metadata(update_data)

    # Read metadata
    metadata = file.metadata

    assert metadata["new_key"] == "new_value"


def test_tulip_file_delete(memory_repo):
    """Test deleting a TulipFile."""
    path = "/test_file_delete.txt"
    data = b"test file content for delete"
    file = TulipFile(path, data, repository=memory_repo)

    # Save the file
    file.save()
    assert memory_repo.tulipfs.exists(path)

    # Delete the file
    file.delete()
    assert not memory_repo.tulipfs.exists(path)
