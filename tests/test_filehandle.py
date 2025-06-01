import io

import pytest

from tulip.filesystem import TulipFileHandle


class TestTulipFileHandle:
    """Tests for the TulipFileHandle class."""

    def test_init(self, tulip_fs, sample_file_path):
        """Test initialization of TulipFileHandle."""
        file_handle = io.BytesIO()
        tulip_handle = TulipFileHandle(file_handle, tulip_fs, sample_file_path, "wb")
        
        assert tulip_handle._handle == file_handle
        assert tulip_handle._tulip_fs == tulip_fs
        assert tulip_handle._path == sample_file_path
        assert tulip_handle._mode == "wb"
        assert not tulip_handle._closed

    def test_write_and_close(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test writing to file handle and closing it."""
        # Create a file handle
        file_handle = io.BytesIO()
        tulip_handle = TulipFileHandle(file_handle, tulip_fs, sample_file_path, "wb")
        
        # Write to the handle
        tulip_handle.write(sample_binary_content)
        
        # Close the handle
        tulip_handle.close()
        
        # Check that the handle is closed
        assert tulip_handle._closed
        assert file_handle.closed

    def test_context_manager(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test using TulipFileHandle as a context manager."""
        file_handle = io.BytesIO()
        
        # Use as context manager
        with TulipFileHandle(file_handle, tulip_fs, sample_file_path, "wb") as handle:
            handle.write(sample_binary_content)
            assert not handle._closed
        
        # Check that the handle is closed after exiting the context
        assert handle._closed
        assert file_handle.closed

    def test_generate_metadata_on_close(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test that metadata is generated when the handle is closed."""
        # Set up the objects filesystem with a file
        tulip_fs.objects_fs.makedirs(str(sample_file_path).rsplit("/", 1)[0], recreate=True)
        tulip_fs.objects_fs.writebytes(sample_file_path, sample_binary_content)
        
        # Create a file handle in write mode
        file_handle = tulip_fs.objects_fs.openbin(sample_file_path, "wb")
        tulip_handle = TulipFileHandle(file_handle, tulip_fs, sample_file_path, "wb")
        
        # Write to the handle and close it
        tulip_handle.write(sample_binary_content)
        tulip_handle.close()
        
        # Check that metadata was generated
        metadata_path = f"{sample_file_path}/tulip.json"
        assert tulip_fs.assets_fs.exists(metadata_path)

    def test_no_metadata_on_read_only(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test that metadata is not generated for read-only handles."""
        # Set up the objects filesystem with a file
        tulip_fs.objects_fs.makedirs(str(sample_file_path).rsplit("/", 1)[0], recreate=True)
        tulip_fs.objects_fs.writebytes(sample_file_path, sample_binary_content)
        
        # Create a file handle in read mode
        file_handle = tulip_fs.objects_fs.openbin(sample_file_path, "rb")
        tulip_handle = TulipFileHandle(file_handle, tulip_fs, sample_file_path, "rb")
        
        # Read from the handle and close it
        tulip_handle.read()
        tulip_handle.close()
        
        # Check that metadata was not generated
        metadata_path = f"{sample_file_path}/tulip.json"
        assert not tulip_fs.assets_fs.exists(metadata_path)

    def test_file_methods(self, tulip_fs, sample_file_path, sample_binary_content):
        """Test that file methods are properly delegated to the underlying handle."""
        # Set up the objects filesystem with a file
        tulip_fs.objects_fs.makedirs(str(sample_file_path).rsplit("/", 1)[0], recreate=True)
        tulip_fs.objects_fs.writebytes(sample_file_path, sample_binary_content)
        
        # Create a file handle
        file_handle = tulip_fs.objects_fs.openbin(sample_file_path, "r+b")
        tulip_handle = TulipFileHandle(file_handle, tulip_fs, sample_file_path, "r+b")
        
        # Test various file methods
        tulip_handle.seek(0)
        assert tulip_handle.tell() == 0
        
        data = tulip_handle.read(5)
        assert len(data) == 5
        
        tulip_handle.seek(0)
        lines = tulip_handle.readlines()
        assert len(lines) > 0
        
        tulip_handle.flush()
        
        assert tulip_handle.readable()
        assert tulip_handle.writable()
        assert tulip_handle.seekable()
        
        # Close the handle
        tulip_handle.close()