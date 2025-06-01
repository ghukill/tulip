import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tulip import TulipFile, TulipObject, TulipRepository
from tulip.objects import TulipEntity


class TestTulipEntity:
    """Tests for the TulipEntity class."""

    def test_update_metadata(self):
        """Test update_metadata updates metadata correctly."""
        # Create a concrete subclass of TulipEntity for testing
        class ConcreteTulipEntity(TulipEntity):
            def generate_metadata(self):
                return {"type": "test", "path": self.path}

            def save(self):
                pass

            def delete(self):
                pass

        # Create a mock repository with a mock tulipfs
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs
        mock_assets_fs = MagicMock()
        mock_tulipfs.assets_fs = mock_assets_fs

        # Mock read_metadata to return a base metadata dict
        base_metadata = {"type": "test", "path": "test/path", "existing_key": "existing_value"}

        # Create a TulipEntity with the mock repository
        entity = ConcreteTulipEntity("test/path", repository=mock_repo)

        # Mock read_metadata to return our base metadata
        with patch.object(entity, 'read_metadata', return_value=base_metadata):
            # Call update_metadata with new metadata
            new_metadata = {"new_key": "new_value", "existing_key": "updated_value"}
            entity.update_metadata(new_metadata)

            # Verify writebytes was called with the updated metadata
            expected_metadata = {
                "type": "test", 
                "path": "test/path", 
                "existing_key": "updated_value",
                "new_key": "new_value"
            }
            mock_assets_fs.writebytes.assert_called_once()

            # Get the actual metadata that was written
            call_args = mock_assets_fs.writebytes.call_args[0]
            assert call_args[0] == "test/path/tulip.json"
            written_metadata = json.loads(call_args[1].decode())

            # Verify the metadata was updated correctly
            assert written_metadata == expected_metadata


class TestTulipObject:
    """Tests for the TulipObject class."""

    def test_init(self):
        """Test initialization of TulipObject."""
        obj = TulipObject("test/path")
        assert obj.path == "test/path"
        assert obj.metadata_path == "test/path/tulip.json"

    def test_get_metadata(self):
        """Test get_metadata returns correct metadata."""
        obj = TulipObject("test/path")
        metadata = obj.generate_metadata()

        assert metadata["type"] == "object"
        assert metadata["path"] == "test/path"
        assert metadata["name"] == "path"
        assert "created_at" in metadata
        assert "updated_at" in metadata

        # Verify timestamps are valid ISO format
        datetime.fromisoformat(metadata["created_at"])
        datetime.fromisoformat(metadata["updated_at"])

    def test_save(self):
        """Test save method creates directory and metadata."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipObject with the mock repository
        obj = TulipObject("test/path", repository=mock_repo)

        # Call save method
        obj.save()

        # Verify makedirs was called
        mock_tulipfs.makedirs.assert_called_once_with("test/path")

    def test_save_with_metadata(self):
        """Test save method with metadata."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipObject with metadata and the mock repository
        metadata = {"custom_key": "custom_value"}
        obj = TulipObject("test/path", metadata_mixins=metadata, repository=mock_repo)

        # Mock update_metadata method
        with patch.object(obj, 'update_metadata') as mock_update_metadata:
            # Call save method
            obj.save()

            # Verify update_metadata was called with the metadata
            mock_update_metadata.assert_called_once_with(metadata)

    def test_delete(self):
        """Test delete method removes directory."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipObject with the mock repository
        obj = TulipObject("test/path", repository=mock_repo)

        # Call delete method
        obj.delete()

        # Verify removetree was called
        mock_tulipfs.removetree.assert_called_once_with("test/path")

    def test_delete_non_recursive(self):
        """Test delete method with recursive=False."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipObject with the mock repository
        obj = TulipObject("test/path", repository=mock_repo)

        # Call delete method with recursive=False
        obj.delete(recursive=False)

        # Verify removedir was called
        mock_tulipfs.removedir.assert_called_once_with("test/path")


class TestTulipFile:
    """Tests for the TulipFile class."""

    def test_init(self):
        """Test initialization of TulipFile."""
        file = TulipFile("test/file.txt")
        assert file.path == "test/file.txt"
        assert file.metadata_path == "test/file.txt/tulip.json"
        assert file.data is None

        file_with_data = TulipFile("test/file.txt", b"test data")
        assert file_with_data.data == b"test data"

    def test_get_metadata_without_data(self):
        """Test get_metadata returns correct metadata when no data is provided."""
        file = TulipFile("test/file.txt")
        metadata = file.generate_metadata()

        assert metadata["type"] == "file"
        assert metadata["path"] == "test/file.txt"
        assert metadata["name"] == "file.txt"
        assert metadata["size"] == 0
        assert metadata["digests"]["sha256"] is None
        assert "created_at" in metadata
        assert "updated_at" in metadata

    def test_get_metadata_with_data(self, sample_binary_content):
        """Test get_metadata returns correct metadata when data is provided."""
        file = TulipFile("test/file.txt", sample_binary_content)
        metadata = file.generate_metadata()

        assert metadata["type"] == "file"
        assert metadata["path"] == "test/file.txt"
        assert metadata["name"] == "file.txt"
        assert metadata["size"] == len(sample_binary_content)
        assert metadata["digests"]["sha256"] is not None
        assert len(metadata["digests"]["sha256"]) == 64  # SHA-256 is 64 hex chars
        assert "created_at" in metadata
        assert "updated_at" in metadata

    def test_get_file_size(self, sample_binary_content):
        """Test _get_file_size returns correct size."""
        file_without_data = TulipFile("test/file.txt")
        assert file_without_data._get_file_size() == 0

        file_with_data = TulipFile("test/file.txt", sample_binary_content)
        assert file_with_data._get_file_size() == len(sample_binary_content)

    def test_get_digests(self, sample_binary_content):
        """Test _get_digests returns correct digests."""
        file_without_data = TulipFile("test/file.txt")
        assert file_without_data._get_digests() == {"sha256": None}

        file_with_data = TulipFile("test/file.txt", sample_binary_content)
        digests = file_with_data._get_digests()
        assert "sha256" in digests
        assert len(digests["sha256"]) == 64  # SHA-256 is 64 hex chars

    def test_save(self, sample_binary_content):
        """Test save method writes file and metadata."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipFile with the mock repository
        file = TulipFile("test/file.txt", sample_binary_content, repository=mock_repo)

        # Call save method
        file.save()

        # Verify writebytes was called with correct arguments
        mock_tulipfs.writebytes.assert_called_once_with("test/file.txt", sample_binary_content)

    def test_save_with_metadata(self, sample_binary_content):
        """Test save method with metadata."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipFile with metadata and the mock repository
        metadata = {"custom_key": "custom_value"}
        file = TulipFile("test/file.txt", sample_binary_content, metadata_mixins=metadata, repository=mock_repo)

        # Mock update_metadata method
        with patch.object(file, 'update_metadata') as mock_update_metadata:
            # Call save method
            file.save()

            # Verify update_metadata was called with the metadata
            mock_update_metadata.assert_called_once_with(metadata)

    def test_delete(self):
        """Test delete method removes file."""
        # Create a mock repository
        mock_repo = MagicMock(spec=TulipRepository)
        mock_tulipfs = MagicMock()
        mock_repo.tulipfs = mock_tulipfs

        # Create a TulipFile with the mock repository
        file = TulipFile("test/file.txt", repository=mock_repo)

        # Call delete method
        file.delete()

        # Verify remove was called
        mock_tulipfs.remove.assert_called_once_with("test/file.txt")
