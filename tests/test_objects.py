import json
from datetime import datetime

import pytest

from tulip import TulipFile, TulipObject


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
        metadata = obj.get_metadata()
        
        assert metadata["type"] == "object"
        assert metadata["path"] == "test/path"
        assert metadata["name"] == "path"
        assert "created_at" in metadata
        assert "updated_at" in metadata
        
        # Verify timestamps are valid ISO format
        datetime.fromisoformat(metadata["created_at"])
        datetime.fromisoformat(metadata["updated_at"])


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
        metadata = file.get_metadata()
        
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
        metadata = file.get_metadata()
        
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