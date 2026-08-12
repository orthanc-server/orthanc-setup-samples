from abc import ABC, abstractmethod
from contextlib import AbstractContextManager

# The sentinel that says "every instance file in this series folder is
# recoverable from the S3 zip named inside it". It is the eviction guard's
# whole basis for deleting a folder, and four modules need to agree on its
# name, so it lives here -- the one module in the plugin that imports nothing.
S3_UPLOADED_MARKER_NAME = ".s3-uploaded"

# Prefix of the temporary file the marker is written through before being
# atomically renamed into place. Anything starting with it is bookkeeping,
# never instance data.
S3_UPLOADED_MARKER_TMP_PREFIX = ".s3-uploaded.tmp-"


class LocalStorageInterface(ABC):

    @abstractmethod
    def lease_folder(self, local_series_folder: str) -> AbstractContextManager[None]:
        pass

    @abstractmethod
    def folder_marker_critical_section(self, local_series_folder: str) -> AbstractContextManager[None]:
        pass

    @abstractmethod
    def write_file(self, local_series_folder: str, uuid: str, content: bytes):
        pass

    @abstractmethod
    def read_file(self, local_series_folder: str, uuid: str) -> bytes:
        pass
