from abc import ABC, abstractmethod

class LocalStorageInterface(ABC):

    @abstractmethod
    def write_file(self, local_series_folder: str, uuid: str, content: bytes):
        pass

    @abstractmethod
    def read_file(self, local_series_folder: str, uuid: str) -> bytes:
        pass
