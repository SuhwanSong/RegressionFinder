import csv
import numpy as np
from os import walk, getenv
from os.path import join, dirname, abspath, exists, basename
from PIL import Image
from PIL import ImageChops
from io import BytesIO
from imagehash import phash

from queue import Queue
from random import choice
from threading import Lock
from collections import defaultdict

from pathlib import Path
from typing import Optional
from shutil import copyfile 
from chrome_binary import build_chrome_binary
from chrome_binary import download_chrome_binary

from domato.grammar import Grammar
from domato.generator import generate_new_sample 

from contextlib import contextmanager

@contextmanager
def acquire_timeout(lock, timeout):
    result = lock.acquire(timeout=timeout)
    yield result
    if result:
        lock.release()

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

        self.limit = 20000

        for testcase, vers in input_version_pair.items():
            self.num_of_inputs += 1
            self.insert_to_queue(vers, testcase, ())

    def reset_lock(self):
        if self.__queue_lock.locked():
            self.__queue_lock.release()
        

    def download_chrome(self, commit_version: int) -> None:
        browser_type = 'chrome'
        self.__queue_lock.acquire()
        parent_dir = FileManager.get_parent_dir(__file__)
        browser_dir = join(parent_dir, browser_type)
        browser_path = join(browser_dir, str(commit_version), browser_type)
        if not exists(browser_path):
            download_chrome_binary(browser_dir, commit_version)
        self.__queue_lock.release()

    def build_chrome(self, commit_version: int) -> None:
        browser_type = 'chrome'
        self.__build_lock.acquire()
        parent_dir = FileManager.get_parent_dir(__file__)
        browser_dir = join(parent_dir, browser_type)
        browser_path = join(browser_dir, str(commit_version), browser_type)
        if not exists(browser_path):
            build_chrome_binary(commit_version)
            pass
        self.__build_lock.release()


    def __select_vers(self) -> Optional[tuple[int, int, int]]:
        keys = list(self.__preqs.keys())
        key =  choice(keys) if keys else None
        return key


    def insert_to_queue(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            value = [html_file, hashes]
            self.__preqs[vers].put(value)

            if not self.__vers: self.__vers = self.__select_vers()

    def pop_from_queue(self) -> Optional[list]:
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            value = None
            if not self.__vers: 
                return
        
            vers = self.__vers
            value = self.__preqs[vers].get()
            if self.__preqs[vers].empty():
                self.__preqs.pop(vers)
                self.__vers = self.__select_vers()
            
            self.num_of_tests += 1
            if self.num_of_tests % 20 == 0:
                print (f'test: {self.num_of_tests}, outputs: {self.num_of_outputs}')
            return value

    def get_vers(self) -> Optional[tuple[int, int, int]]:
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            vers = self.__vers
            return vers

    def update_postq(self, vers: tuple[int, int, int], html_file: str, hashes: tuple) -> None:
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            self.__postqs[vers].put((html_file, hashes))
            self.num_of_outputs += 1
            if self.num_of_outputs >= self.limit:
                self.__preqs.clear()
                self.__vers = self.__select_vers()

    def move_to_preqs(self):
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            self.__preqs.clear()
            self.__preqs = self.__postqs.copy()
            self.__postqs.clear()
            self.__vers = self.__select_vers()
            self.num_of_inputs = self.num_of_outputs
            self.num_of_tests = 0
            self.num_of_outputs = 0

    def dump_queue(self, dir_path):
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 

            Path(dir_path).mkdir(parents=True, exist_ok=True)
            keys = list(self.__preqs.keys())
            for vers in keys:
                q = self.__preqs[vers]
                length = len(list(q.queue))
                for _ in range(length):
                    html_file, hashes = q.get()
                    name = basename(html_file)
                    new_html_file = join(dir_path, name)
                    copyfile(html_file, new_html_file)
                    q.put((new_html_file, hashes))
    

    def dump_queue_as_csv(self, path):
        header = ['base', 'target', 'ref', 'file']
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            with open(path, 'w') as fp:
                c = csv.writer(fp)
                c.writerow(header)
                keys = self.__preqs.keys()
                for key in keys:
                    q = self.__preqs[key]
                    for value in list(q.queue):
                        html_file, hashes = value
                        base, target, ref = key
                        c.writerow([str(base), str(target), str(ref), html_file])


    def dump_queue_with_sort(self, dir_path):
        with acquire_timeout(self.__queue_lock, 1000) as acquired:
            if not acquired: return 
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            keys = self.__preqs.keys()
            for vers in keys:
                q = self.__preqs[vers]
                length = q.qsize()
                cur_path = join(dir_path, str(vers[1]))
                Path(cur_path).mkdir(parents=True, exist_ok=True)
                for _ in range(length):
                    html_file, hashes = q.get()
                    name = basename(html_file)
                    new_html_file = join(cur_path, name)
                    copyfile(html_file, new_html_file)
                    q.put((new_html_file, hashes))


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
    def __init__(self):
        domato_dir = join(dirname(abspath(__file__)), 'domato')
        f = open(os.path.join(domato_dir, 'template.html'))
        self.template = f.read()
        f.close()
        htmlgrammar = Grammar()
        err = htmlgrammar.parse_from_file(os.path.join(domato_dir, 'html.txt'))
        if err > 0:
            print('There were errors parsing grammar')
            return
        cssgrammar = Grammar()
        err = cssgrammar.parse_from_file(os.path.join(domato_dir, 'css.txt'))
        if err > 0:
            print('There were errors parsing grammar')
            return
        htmlgrammar.add_import('cssgrammar', cssgrammar)
        self.htmlgrammar = htmlgrammar
        self.cssgrammar = cssgrammar

    def generate_html(self):
        return generate_new_sample(
                self.template, 
                self.htmlgrammar, 
                self.cssgrammar, 
                None)


class ImageDiff:
    def get_phash(png):
        return png

    def diff_images(hash_A, hash_B):
        return hash_A != hash_B

    def save_image(name, png):
        stream = BytesIO(png)
        im = Image.open(stream, 'r')
        im.save(name)
        im.close()


MILESTONE = {
    79: 706915,
    80: 722274,
    81: 737173,
    82: 749737,
    83: 756066,
    84: 768962,
    85: 782793,
    86: 800218,
    87: 812852,
    88: 827102,
    89: 843830,
    90: 857950,
    91: 870763,
    92: 885287,
    93: 902210,
    94: 911515,
    95: 920003,
    96: 929512,
    97: 938553,
    98: 950365,
    99: 961656,
    100: 972766,
    101: 982481,
    102: 992738,
    103:1002911,
    104:1006827
}
