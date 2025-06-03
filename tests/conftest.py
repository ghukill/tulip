import pytest
from pathlib import Path
import tempfile

from tulip.repository import TulipRepository


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def memory_repo():
    """Provide a TulipRepository using in-memory storage."""
    repo = TulipRepository.from_memory()
    return repo


@pytest.fixture
def local_repo(temp_dir):
    """Provide a TulipRepository using local filesystem storage."""
    repo = TulipRepository.from_local_root_directory(temp_dir)
    return repo