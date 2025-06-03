# DEBUG ------------------------------------------------------------------------
from tulip import TulipRepository

tr = TulipRepository.from_local_root_path("/tmp/tulip")

tr.tulipfs.removetree("images")

tr.tulipfs.makedir("images")
tr.tulipfs.makedirs("images/dogs/small")
tr.tulipfs.makedirs("images/dogs/large")
tr.tulipfs.makedir("images/cats")
tr.tulipfs.makedir("images/cats/huge")

with tr.tulipfs.openbin("images/dogs/large/smokey.txt", "w") as f:
    f.write(b"BIG DOG.")


# DEBUG ------------------------------------------------------------------------
from tulip import TulipRepository

tr = TulipRepository.from_filesystems(
    object_fs="mem://",
    asset_fs="mem://",
)

# DEBUG ------------------------------------------------------------------------
from fs.copy import copy_dir
from fs.zipfs import ZipFS
from tulip import TulipRepository

tr = TulipRepository.from_local_root_path("/tmp/tulip")

gp = ZipFS(
    "/Users/commander/dev/data/google_photos_takeout_2025_01_16/takeout-20250116T143917Z-001.zip"
)

copy_dir(gp, "/", tr.tulipfs, "/takeout-20250116T143917Z-001")

# DEBUG ------------------------------------------------------------------------

from tulip import TulipRepository

tr = TulipRepository.from_memory()

o = tr.create_object("horse", {"pickles": True})
f = tr.create_file("horse/hi.txt", b"what the deuce")

o2 = tr.create_object("horse/details", {"pickles": True})
o3 = tr.create_object("horse/details/for_sure", {"pickles": True})
f2 = tr.create_file(
    "horse/details/woah.txt", b"what the deuce", metadata={"tennis": "fun"}
)

tr.delete_object("horse", recursive=True)

# DEBUG ------------------------------------------------------------------------

from fs import open_fs
from fs.copy import copy_dir
from tulip import TulipRepository

tr = TulipRepository.from_memory()

remote = open_fs("ssh://commander:<PASSWORD>@192.168.1.141:/home/commander/tmp")

copy_dir(remote, "/me_goobers", tr.tulipfs, "/me_goobers")

# DEBUG ------------------------------------------------------------------------

from fs_s3fs import S3FS

from tulip import TulipRepository

object_fs = S3FS(
    "tulips-personal",
    dir_path="objects",
    aws_access_key_id="...",
    aws_secret_access_key="...",
)
asset_fs = S3FS(
    "tulips-personal",
    dir_path="assets",
    aws_access_key_id="...",
    aws_secret_access_key="...",
)

tr = TulipRepository.from_filesystems(object_fs=object_fs, asset_fs=asset_fs)

o = tr.create_object("horse", {"pickles": True})
f = tr.create_file("horse/hi.txt", b"what the deuce")

o2 = tr.create_object("horse/details", {"pickles": True})
o3 = tr.create_object("horse/details/for_sure", {"pickles": True})
f2 = tr.create_file(
    "horse/details/woah.txt", b"what the deuce", metadata={"tennis": "fun"}
)
