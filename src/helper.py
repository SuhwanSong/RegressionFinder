import csv

from os import walk
from os.path import join, dirname, abspath, exists

from PIL import Image
from io import BytesIO
from imagehash import phash

from queue import Queue
from random import choice
from threading import Lock
from collections import defaultdict

from typing import Optional
from shutil import copyfile 
from download_version import download_chrome

class IOQueue:
    def __init__(self, input_version_pair: dict[str, tuple[int, int, int]]) -> None:

        self.__build_lock = Lock()
        self.__queue_lock = Lock()
        self.__preqs = defaultdict(Queue)
        self.__postqs = defaultdict(Queue)
        self.__vers = None

        self.num_of_tests = 0
        self.num_of_inputs = 0
        self.num_of_outputs = 0

        for testcase, vers in input_version_pair.items():
            self.num_of_inputs += 1
            self.insert_to_queue(vers, testcase, ())

    def get_chrome(self, commit_version: int) -> None:
        browser_type = 'chrome'
        self.__build_lock.acquire()
        parent_dir = FileManager.get_parent_dir(__file__)
        browser_dir = join(parent_dir, browser_type)
        browser_path = join(browser_dir, str(commit_version), browser_type)
        if not exists(browser_path):
            download_chrome(browser_dir, commit_version)
        self.__build_lock.release()

    def __select_vers(self) -> Optional[tuple[int, int, int]]:
        keys = list(self.__preqs.keys())
        return choice(keys) if keys else None

    def insert_to_queue(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        self.__queue_lock.acquire()
        value = [html_file, hashes]
        self.__preqs[vers].put(value)

        if not self.__vers: self.__vers = self.__select_vers()

        self.__queue_lock.release()

    def pop_from_queue(self) -> Optional[list]:
        if not self.__vers: return

        value = None
        self.__queue_lock.acquire()

        vers = self.__vers
        value = self.__preqs[vers].get()
        if self.__preqs[vers].empty():
            self.__preqs.pop(vers)
            self.__vers = self.__select_vers()
        
        self.num_of_tests += 1
        if self.num_of_tests % 100 == 0:
            print (f'test: {self.num_of_tests}, outputs: {self.num_of_outputs}')
        self.__queue_lock.release()
        return value

    def get_vers(self) -> Optional[tuple[int, int, int]]:
        self.__queue_lock.acquire()
        vers = self.__vers
        self.__queue_lock.release()
        return vers

    def update_postq(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        self.__queue_lock.acquire()
        self.num_of_outputs += 1
        self.__postqs[vers].put((html_file, hashes))
        self.__queue_lock.release()

    def move_to_preqs(self):
        self.__queue_lock.acquire()
        self.__preqs.clear()
        self.__preqs = self.__postqs.copy()
        self.__postqs.clear()
        self.__vers = self.__select_vers()
        self.num_of_inputs = self.num_of_outputs
        self.num_of_tests = 0
        self.num_of_outputs = 0
        self.__queue_lock.release()

    def dump_queue(self, dir_path):
        num = 0
        self.__queue_lock.acquire()
        for vers, q in self.__postqs.items():
            length = q.qsize()
            for _ in range(length):
                html_file, hashes = q.get()
                name = 'id-' + str(num).zfill(6)
                new_html_file = join(dir_path, f'{name}.html')
                copyfile(html_file, new_html_file)
                q.put((new_html_file, hashes))
                num += 1

        self.__queue_lock.release()

    def dump_queue_as_csv(self, path):
        header = ['base', 'target', 'ref', 'file']
        self.__queue_lock.acquire()
        with open(path, 'w') as fp:
            c = csv.writer(fp)
            c.writerow(header)
            for key, q in self.__postqs.items():
                for value in list(q.queue):
                    html_file, hashes = value
                    base, target, ref = key
                    c.writerow([str(base), str(target), str(ref), html_file])
               
        self.__queue_lock.release()


class FileManager:
    def get_all_files(root, ext=None):
        paths = []
        for path, subdirs, files in walk(root):
            for name in files:
                if ext is not None and ext not in name:
                    continue
                paths.append((join(path, name)))
        return paths

    def get_bisect_csv():
        csvfile = join(
                dirname(dirname(abspath(__file__))),
                'data', 
                'bisect-builds-cache.csv')
        tmp = []
        with open(csvfile, 'r') as fp:
            line = fp.readline()
            vers = line.split(', ')
            for ver in vers:
                tmp.append(int(ver))
        tmp.sort()
        return tmp

    def get_parent_dir(file):
        return dirname(dirname(abspath(file)))

    def write_file(name, content):
        with open(name, 'w') as fp:
            fp.write(content)

    def read_file(name):
        with open(name, 'r') as fp:
            return fp.read()


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
        THRE = 4 # 16
        return hash_A - hash_B  > THRE
