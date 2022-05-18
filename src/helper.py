import os

from PIL import Image
from io import BytesIO
from imagehash import phash

from random import choice

from queue import Queue
from threading import Lock
from collections import defaultdict

from typing import Optional


class IOQueue:
    def __init__(self, vers: tuple[int, int, int], inputs: list) -> None:

        self.__lock = Lock()
        self.__preqs = defaultdict(Queue)
        self.__postqs = defaultdict(Queue)

        for testcase in inputs:
            self.__preqs[vers].put((testcase, ()))

        self.__vers = self.__select_vers()

    def __select_vers(self) -> Optional[tuple[int, int, int]]:
        keys = list(self.__preqs.keys())
        return choice(keys) if keys else None

    def insert_to_queue(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        self.__lock.acquire()
        value = [html_file, hashes]
        self.__preqs[vers].put(value)

        self.__lock.release()

    def pop_from_queue(self) -> Optional[list]:
        if not self.__vers: return

        value = None
        self.__lock.acquire()

        vers = self.__vers
        value = self.__preqs[vers].get()
        if self.__preqs[vers].empty():
            self.__preqs.pop(vers)
            self.__vers = self.__select_vers()

        self.__lock.release()
        return value

    def get_vers(self) -> Optional[tuple[int, int, int]]:
        self.__lock.acquire()
        vers = self.__vers
        self.__lock.release()
        return vers

    def update_postq(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        self.__lock.acquire()
        self.__postqs[vers].put((html_file, hashes))
        self.__lock.release()

    def move_to_preqs(self):
        self.__lock.acquire()
        self.__preqs.clear()
        self.__preqs = self.__postqs.copy()
        self.__postqs.clear()
        self.__vers = self.__select_vers()
        self.__lock.release()


class FileManager:
    def get_all_files(root, ext=None):
        paths = []
        for path, subdirs, files in os.walk(root):
            for name in files:
                if ext is not None and ext not in name:
                    continue
                paths.append((os.path.join(path, name)))
        return paths


class Generator:
    def __init__(self, num_of_inputs):
        pass


class ImageDiff:
    def get_phash(png):
        HASHSIZE = 16
        stream = png if isinstance(png, str) else BytesIO(png)
        with Image.open(stream, 'r') as image:
            hash_v = phash(image, hash_size = HASHSIZE)
            return hash_v

    def diff_images(hash_A, hash_B):
        THRE = 8 # 16
        return hash_A - hash_B  > THRE
