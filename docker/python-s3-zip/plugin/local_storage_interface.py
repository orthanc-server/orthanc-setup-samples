from abc import ABC, abstractmethod

class LocalStorageInterface(ABC):

    @abstractmethod
    def write_file(self, uuid: str, content: bytes):
        pass

    @abstractmethod
    def read_file(self, uuid: str) -> bytes:
        pass
