import os
import tempfile
from pathlib import Path

import pytest
from fs.memoryfs import MemoryFS

from tulip import TulipFS, TulipRepository


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def objects_memfs():
    """Provide a memory filesystem for objects."""
    return MemoryFS()


@pytest.fixture
def assets_memfs():
    """Provide a memory filesystem for assets."""
    return MemoryFS()


@pytest.fixture
def tulip_fs(objects_memfs, assets_memfs):
    """Provide a TulipFS instance with memory filesystems."""
    return TulipFS(objects_memfs, assets_memfs)


@pytest.fixture
def local_repo_path(temp_dir):
    """Provide a path for a local repository."""
    repo_path = temp_dir / "tulip_repo"
    repo_path.mkdir(exist_ok=True)
    return repo_path


@pytest.fixture
def local_repo(local_repo_path):
    """Provide a TulipRepository instance with local filesystem."""
    return TulipRepository.from_local_root_path(local_repo_path)


@pytest.fixture
def memory_repo(objects_memfs, assets_memfs):
    """Provide a TulipRepository instance with memory filesystems."""
    return TulipRepository.from_filesystems(objects_memfs, assets_memfs)


@pytest.fixture
def sample_text_content():
    """Provide sample text content for testing."""
    return "This is a sample text file for testing."


@pytest.fixture
def sample_binary_content():
    """Provide sample binary content for testing."""
    return b"This is a sample binary file for testing."


@pytest.fixture
def sample_file_path():
    """Provide a sample file path for testing."""
    return "test_dir/test_file.txt"


@pytest.fixture
def sample_dir_path():
    """Provide a sample directory path for testing."""
    return "test_dir"


@pytest.fixture
def nested_dir_path():
    """Provide a nested directory path for testing."""
    return "parent/child/grandchild"