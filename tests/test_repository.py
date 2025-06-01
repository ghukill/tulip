import os
from pathlib import Path

import pytest
from fs.memoryfs import MemoryFS

from tulip import TulipRepository


class TestTulipRepositoryInitialization:
    """Tests for TulipRepository initialization."""

    def test_init_with_explicit_paths(self, temp_dir):
        """Test initialization with explicit filesystem paths."""
        objects_path = temp_dir / "objects"
        assets_path = temp_dir / "assets"

        # Create directories first
        objects_path.mkdir(parents=True, exist_ok=True)
        assets_path.mkdir(parents=True, exist_ok=True)

        repo = TulipRepository(f"osfs://{objects_path}", f"osfs://{assets_path}")

        assert repo.tulipfs is not None
        assert repo.tulipfs.objects_fs is not None
        assert repo.tulipfs.assets_fs is not None

    def test_from_local_root_path(self, temp_dir):
        """Test creating repository from local root path."""
        repo = TulipRepository.from_local_root_path(temp_dir)

        # Check that the repository was created
        assert repo.tulipfs is not None

        # Check that the objects and assets directories were created
        objects_dir = temp_dir / "objects"
        assets_dir = temp_dir / "assets"
        assert objects_dir.exists() and objects_dir.is_dir()
        assert assets_dir.exists() and assets_dir.is_dir()

    def test_from_filesystems(self):
        """Test creating repository from filesystem URIs."""
        repo = TulipRepository.from_filesystems("mem://", "mem://")

        assert repo.tulipfs is not None
        assert repo.tulipfs.objects_fs is not None
        assert repo.tulipfs.assets_fs is not None


class TestTulipRepositoryOperations:
    """Tests for TulipRepository operations through TulipFS."""

    def test_file_operations(self, local_repo, sample_file_path, sample_text_content):
        """Test file operations through repository."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        local_repo.tulipfs.makedirs(parent_dir, recreate=True)

        # Write a file
        local_repo.tulipfs.writetext(sample_file_path, sample_text_content)

        # Check file exists
        assert local_repo.tulipfs.exists(sample_file_path)

        # Read file
        content = local_repo.tulipfs.readtext(sample_file_path)
        assert content == sample_text_content

        # Remove file
        local_repo.tulipfs.remove(sample_file_path)
        assert not local_repo.tulipfs.exists(sample_file_path)

    def test_directory_operations(self, local_repo, nested_dir_path):
        """Test directory operations through repository."""
        # Create nested directories
        local_repo.tulipfs.makedirs(nested_dir_path)

        # Check directories exist
        assert local_repo.tulipfs.exists(nested_dir_path)

        # Create a file in the nested directory
        file_path = f"{nested_dir_path}/test.txt"
        local_repo.tulipfs.writetext(file_path, "test content")

        # List directory contents
        parent_dir = Path(nested_dir_path).parts[0]
        assert "child" in local_repo.tulipfs.listdir(parent_dir)

        # Remove directory tree
        local_repo.tulipfs.removetree(parent_dir)
        assert not local_repo.tulipfs.exists(parent_dir)


class TestTulipRepositoryIntegration:
    """Integration tests for TulipRepository."""

    def test_repository_persistence(self, temp_dir):
        """Test that repository data persists between instances."""
        repo_path = temp_dir / "persistence_test"
        repo_path.mkdir()

        # Create a repository and add a file (no need to create parent directory for root-level file)
        repo1 = TulipRepository.from_local_root_path(repo_path)
        repo1.tulipfs.writetext("test.txt", "test content")

        # Create a new repository instance pointing to the same location
        repo2 = TulipRepository.from_local_root_path(repo_path)

        # Check that the file exists in the new instance
        assert repo2.tulipfs.exists("test.txt")
        assert repo2.tulipfs.readtext("test.txt") == "test content"

    def test_repository_with_memory_fs(self):
        """Test repository with memory filesystems."""
        # Create repository with memory filesystems
        objects_fs = MemoryFS()
        assets_fs = MemoryFS()

        repo = TulipRepository(objects_fs, assets_fs)

        # Add a file (no need to create parent directory for root-level file)
        repo.tulipfs.writetext("test.txt", "test content")

        # Check file exists in both filesystems
        assert objects_fs.exists("test.txt")
        assert assets_fs.exists("test.txt/tulip.json")

        # Check content
        assert objects_fs.readtext("test.txt") == "test content"
