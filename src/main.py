import argparse

from random import seed

from helper import IOQueue
from helper import FileManager

from modules import CrossVersion
from modules import Oracle
from modules import Bisecter


class R2Z2:
    def __init__(self, vers: tuple[int, int, int], inputs: list, output_dir: str, num_of_threads: int):

        self.__ioq = IOQueue(vers, inputs)
        self.__out_dir = output_dir
        self.__num_of_threads = num_of_threads


    def __test_wrapper(self, test_class: object):
        threads = []
        for i in range(self.__num_of_threads):
            threads.append(test_class(self.__ioq))

        for th in threads:
            th.start()

        for th in threads:
            th.join()
        self.__ioq.move_to_preqs()

    def process(self):
        self.__test_wrapper(CrossVersion)
        self.__test_wrapper(Oracle)
        self.__test_wrapper(Bisecter)


def main():
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-s', '--start', required=True, type=int, help='start chrome commit')
    parser.add_argument('-e', '--end', required=True, type=int, help='end chrome commit')
    parser.add_argument('-f', '--firefox', required=True, type=int, help='firefox commit')
    parser.add_argument('-r', '--randomseed', required=False, type=int, default=0, help='random seed')
    parser.add_argument('-i', '--input', required=False, type=str, default='', help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=1, help='number of threads')
    args = parser.parse_args()

    seed(args.randomseed)

    if args.input:
        inputs = FileManager.get_all_files(args.input)
    else:
        pass # TODO

    vers = (args.start, args.end, args.firefox)
    output_dir = args.output
    num_of_threads = args.job

    R2Z2(vers, inputs, output_dir, num_of_threads).process()

if __name__ == "__main__":
    main()
