import hashlib
from os import listdir, makedirs, path, remove
from typing import Optional


class Cache:

    class CacheException(Exception):
        def __init__(self, message: str, source_exception: Exception = None):
            self.source_exception = source_exception
            super().__init__(message)

    def __init__(self, base_path: str = 'cache/'):
        self.__base_path = base_path

    def __get_file_path(self, id: str) -> str:
        hash = hashlib.sha1()
        hash.update(id.encode('utf-8'))
        return path.join(self.__base_path, hash.hexdigest())

    def setup(self) -> None:
        try:
            makedirs(self.__base_path, exist_ok=True)
        except OSError as e:
            raise Cache.CacheException(
                'Could not create the cache directory: {}'.format(
                    self.__base_path),
                e)

    def read(self, id: str) -> Optional[str]:
        data = None
        file_path = self.__get_file_path(id)
        try:
            file = open(file_path, 'r')
            data = file.read()
            file.close()
        except FileNotFoundError:
            pass
        except OSError as e:
            raise Cache.CacheException(
                'Could not read from the file: {}'.format(file_path), e)
        return data

    def write(self, id: str, data: str):
        file_path = self.__get_file_path(id)
        try:
            file = open(file_path, 'w')
            file.write(data)
            file.close()
        except OSError as e:
            raise Cache.CacheException(
                'Could not write to the file: {}'.format(file_path), e)

    def clear(self):
        for file_name in listdir(self.__base_path):
            file_path = path.join(self.__base_path, file_name)
            try:
                if path.isfile(file_path):
                    remove(file_path)
            except Exception as e:
                raise Cache.CacheException(
                    'Could not delete the file: {}'.format(file_path), e)
