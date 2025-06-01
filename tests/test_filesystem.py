import json
from pathlib import Path

import pytest
from fs.errors import ResourceNotFound

from tulip import TulipFS


class TestTulipFSInitialization:
    """Tests for TulipFS initialization."""

    def test_init_with_fs_instances(self, objects_memfs, assets_memfs):
        """Test initialization with FS instances."""
        fs = TulipFS(objects_memfs, assets_memfs)
        assert fs.objects_fs == objects_memfs
        assert fs.assets_fs == assets_memfs

    def test_init_with_fs_uris(self, temp_dir):
        """Test initialization with FS URIs."""
        objects_path = temp_dir / "objects"
        assets_path = temp_dir / "assets"
        objects_path.mkdir()
        assets_path.mkdir()

        fs = TulipFS(f"osfs://{objects_path}", f"osfs://{assets_path}")
        assert fs.objects_fs is not None
        assert fs.assets_fs is not None

    def test_init_with_invalid_fs(self):
        """Test initialization with invalid FS."""
        with pytest.raises(ValueError, match="A PyFilesystem instance or URI required"):
            TulipFS(123, "osfs://temp")


class TestTulipFSDirectoryOperations:
    """Tests for TulipFS directory operations."""

    def test_makedir(self, tulip_fs, sample_dir_path):
        """Test makedir creates directory and metadata."""
        tulip_fs.makedir(sample_dir_path)

        # Check directory exists in objects filesystem
        assert tulip_fs.objects_fs.isdir(sample_dir_path)

        # Check metadata exists in assets filesystem
        metadata_path = f"{sample_dir_path}/tulip.json"
        assert tulip_fs.assets_fs.exists(metadata_path)

        # Check metadata content
        metadata_content = json.loads(tulip_fs.assets_fs.readtext(metadata_path))
        assert metadata_content["type"] == "object"
        assert metadata_content["path"] == sample_dir_path

    def test_makedirs(self, tulip_fs, nested_dir_path):
        """Test makedirs creates nested directories and metadata."""
        tulip_fs.makedirs(nested_dir_path)

        # Check all directories exist in objects filesystem
        path_parts = Path(nested_dir_path).parts
        current_path = ""

        for part in path_parts:
            current_path = str(Path(current_path) / part)
            assert tulip_fs.objects_fs.isdir(current_path)

            # Check metadata exists for each directory
            metadata_path = f"{current_path}/tulip.json"
            assert tulip_fs.assets_fs.exists(metadata_path)

            # Check metadata content
            metadata_content = json.loads(tulip_fs.assets_fs.readtext(metadata_path))
            assert metadata_content["type"] == "object"
            assert metadata_content["path"] == current_path

    def test_removedir(self, tulip_fs, sample_dir_path):
        """Test removedir removes directory and metadata."""
        # Create directory first
        tulip_fs.makedir(sample_dir_path)
        assert tulip_fs.objects_fs.isdir(sample_dir_path)
        assert tulip_fs.assets_fs.exists(f"{sample_dir_path}/tulip.json")

        # Remove directory
        tulip_fs.removedir(sample_dir_path)

        # Check directory and metadata are removed
        assert not tulip_fs.objects_fs.exists(sample_dir_path)
        assert not tulip_fs.assets_fs.exists(sample_dir_path)

    def test_removetree(self, tulip_fs, nested_dir_path):
        """Test removetree removes directory tree and metadata."""
        # Create nested directories first
        tulip_fs.makedirs(nested_dir_path)

        # Create a file in the nested directory
        file_path = f"{nested_dir_path}/test.txt"
        tulip_fs.writetext(file_path, "test content")

        # Remove directory tree
        parent_dir = Path(nested_dir_path).parts[0]
        tulip_fs.removetree(parent_dir)

        # Check directory tree and metadata are removed
        assert not tulip_fs.objects_fs.exists(parent_dir)
        assert not tulip_fs.assets_fs.exists(parent_dir)


class TestTulipFSFileOperations:
    """Tests for TulipFS file operations."""

    def test_writebytes(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test writebytes writes file content and metadata."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Check file exists and has correct content
        assert tulip_fs.objects_fs.exists(sample_file_path)
        assert tulip_fs.objects_fs.readbytes(sample_file_path) == sample_binary_content

        # Check metadata exists
        metadata_path = f"{sample_file_path}/tulip.json"
        assert tulip_fs.assets_fs.exists(metadata_path)

        # Check metadata content
        metadata_content = json.loads(tulip_fs.assets_fs.readtext(metadata_path))
        assert metadata_content["type"] == "file"
        assert metadata_content["path"] == sample_file_path
        assert metadata_content["size"] == len(sample_binary_content)
        assert "sha256" in metadata_content["digests"]

    def test_writetext(self, tulip_fs, sample_file_path, sample_text_content):
        """Test writetext writes file content and metadata."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        tulip_fs.writetext(sample_file_path, sample_text_content)

        # Check file exists and has correct content
        assert tulip_fs.objects_fs.exists(sample_file_path)
        assert tulip_fs.objects_fs.readtext(sample_file_path) == sample_text_content

        # Check metadata exists
        metadata_path = f"{sample_file_path}/tulip.json"
        assert tulip_fs.assets_fs.exists(metadata_path)

        # Check metadata content
        metadata_content = json.loads(tulip_fs.assets_fs.readtext(metadata_path))
        assert metadata_content["type"] == "file"
        assert metadata_content["path"] == sample_file_path

    def test_readbytes(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test readbytes reads file content."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Write file first
        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Read file
        content = tulip_fs.readbytes(sample_file_path)
        assert content == sample_binary_content

    def test_readtext(self, tulip_fs, sample_file_path, sample_text_content):
        """Test readtext reads file content."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Write file first
        tulip_fs.writetext(sample_file_path, sample_text_content)

        # Read file
        content = tulip_fs.readtext(sample_file_path)
        assert content == sample_text_content

    def test_remove(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test remove removes file and metadata."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Write file first
        tulip_fs.writebytes(sample_file_path, sample_binary_content)
        assert tulip_fs.objects_fs.exists(sample_file_path)
        assert tulip_fs.assets_fs.exists(f"{sample_file_path}/tulip.json")

        # Remove file
        tulip_fs.remove(sample_file_path)

        # Check file and metadata are removed
        assert not tulip_fs.objects_fs.exists(sample_file_path)
        assert not tulip_fs.assets_fs.exists(sample_file_path)

    def test_openbin(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test openbin opens file for reading and writing."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Test writing with openbin
        with tulip_fs.openbin(sample_file_path, "wb") as f:
            f.write(sample_binary_content)

        # Check file exists and has correct content
        assert tulip_fs.objects_fs.exists(sample_file_path)
        assert tulip_fs.objects_fs.readbytes(sample_file_path) == sample_binary_content

        # Check metadata exists
        metadata_path = f"{sample_file_path}/tulip.json"
        assert tulip_fs.assets_fs.exists(metadata_path)

        # Test reading with openbin
        with tulip_fs.openbin(sample_file_path, "rb") as f:
            content = f.read()
        assert content == sample_binary_content


class TestTulipFSInfoOperations:
    """Tests for TulipFS information operations."""

    def test_exists(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test exists checks if path exists."""
        # Path doesn't exist initially
        assert not tulip_fs.exists(sample_file_path)

        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Create file
        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Path exists now
        assert tulip_fs.exists(sample_file_path)

    def test_isfile(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test isfile checks if path is a file."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Create file
        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Create a different directory (not the same path as the file)
        test_dir_path = "test_dir2"
        tulip_fs.makedir(test_dir_path)

        # Check isfile
        assert tulip_fs.isfile(sample_file_path)
        assert not tulip_fs.isfile(test_dir_path)

    def test_isdir(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test isdir checks if path is a directory."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Create file
        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Create a different directory (not the same path as the file)
        test_dir_path = "test_dir3"
        tulip_fs.makedir(test_dir_path)

        # Check isdir
        assert not tulip_fs.isdir(sample_file_path)
        assert tulip_fs.isdir(test_dir_path)

    def test_listdir(self, tulip_fs, sample_dir_path):
        """Test listdir lists directory contents."""
        # Create directory with files
        tulip_fs.makedir(sample_dir_path)
        tulip_fs.writetext(f"{sample_dir_path}/file1.txt", "content1")
        tulip_fs.writetext(f"{sample_dir_path}/file2.txt", "content2")
        tulip_fs.makedir(f"{sample_dir_path}/subdir")

        # List directory
        contents = tulip_fs.listdir(sample_dir_path)
        assert sorted(contents) == sorted(["file1.txt", "file2.txt", "subdir"])


class TestTulipFSErrorHandling:
    """Tests for TulipFS error handling."""

    def test_read_nonexistent_file(self, tulip_fs, sample_file_path):
        """Test reading a nonexistent file raises ResourceNotFound."""
        with pytest.raises(ResourceNotFound):
            tulip_fs.readbytes(sample_file_path)

    def test_remove_nonexistent_file(self, tulip_fs, sample_file_path):
        """Test removing a nonexistent file raises ResourceNotFound."""
        with pytest.raises(ResourceNotFound):
            tulip_fs.remove(sample_file_path)

    def test_removedir_nonexistent_dir(self, tulip_fs, sample_dir_path):
        """Test removing a nonexistent directory raises ResourceNotFound."""
        with pytest.raises(ResourceNotFound):
            tulip_fs.removedir(sample_dir_path)

    def test_makedir_existing_file(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test making a directory at an existing file path raises an error."""
        # Create parent directory first
        parent_dir = str(sample_file_path).rsplit("/", 1)[0]
        tulip_fs.makedirs(parent_dir, recreate=True)

        # Create file first
        tulip_fs.writebytes(sample_file_path, sample_binary_content)

        # Try to create directory at same path
        with pytest.raises(Exception):
            tulip_fs.makedir(sample_file_path)
