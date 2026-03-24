import sys
import os

# When this directory is used as a Python package (e.g., via a symlink named
# "s3zipstorage"), the modules inside use flat/absolute imports such as
# "from s3_zip_storage import S3ZipStorage". Adding the package directory to
# sys.path allows these imports to resolve without modifying the vendored files
# from Alain's code.
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
