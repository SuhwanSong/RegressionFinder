import argparse

from random import seed
from helper import FileManager
from helper import MILESTONE

from modules import Finder

def main():
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-b', '--base', required=True, type=int, help='milestone')
    parser.add_argument('-t', '--target', required=True, type=int, help='milestone')
    parser.add_argument('-f', '--firefox', required=True, type=int, help='firefox commit')
    parser.add_argument('-a', '--answer', required=True, type=int, help='firefox commit')
    parser.add_argument('-r', '--randomseed', required=False, type=int, default=0, help='random seed')
    parser.add_argument('-i', '--input', required=False, type=str, default='', help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=1, help='number of threads')
    args = parser.parse_args()

    seed(args.randomseed)

    inputs = FileManager.get_all_files(args.input, '.html')
    print ('# of initial inputs: ', len(inputs))
    versions = FileManager.get_bisect_csv()
    milestone = MILESTONE

    import bisect

    # 94 --> after 93 ~ before 95 
    base = bisect.bisect_right(versions, milestone[args.base])
    target = bisect.bisect_left(versions, milestone[args.target])
    answer = bisect.bisect_right(versions, milestone[args.answer])
    answer = versions[answer]
    
    vers = (versions[base], versions[target], args.firefox)
    output_dir = args.output
    num_of_threads = args.job

    input_version_pair = {}

    for inp in inputs:
      input_version_pair[inp] = vers
    Finder(input_version_pair, output_dir, num_of_threads, answer).process()

if __name__ == "__main__":
    main()
