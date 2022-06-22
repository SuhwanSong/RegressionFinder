import shutil
import argparse

from os.path import join, exists
from random import seed
from helper import FileManager

from modules import Preprocesser
from modules import Finder
from modules import ChromeRegression

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
    milestone = {
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

    import bisect

    base = bisect.bisect_right(versions, milestone[args.base])
    target = bisect.bisect_left(versions, milestone[args.target])
    answer = bisect.bisect_right(versions, milestone[args.answer])
    answer = versions[answer]
    
    vers = (versions[base], versions[target], args.firefox)
    output_dir = args.output
    num_of_threads = args.job

    min_dir = join(output_dir, 'Minimizer')
    print ('min_dir', min_dir)
#    if not exists(min_dir):
#        cv_dir = join(output_dir, 'CrossVersion')
#        if exists(cv_dir): shutil.rmtree(cv_dir)
#        input_version_pair = {}
#        for inp in inputs:
#            input_version_pair[inp] = vers
#        Preprocesser(input_version_pair, output_dir, num_of_threads).process()

    input_version_pair = {}
    inputs = FileManager.get_all_files(min_dir, '.html')
    print ('# of initial inputs: ', len(inputs))
    versions = FileManager.get_bisect_csv()
    for inp in inputs:
      input_version_pair[inp] = vers
   
    finder_dir = output_dir + '_test'
    if exists(finder_dir):
        shutil.rmtree(finder_dir)
    finder = Finder(input_version_pair,finder_dir, num_of_threads, answer)
    finder.process()


    input_version_pair = {}
    vers = (versions[base], versions[target], answer)
    for inp in inputs:
      input_version_pair[inp] = vers

    oracle_dir = output_dir + '_oracle'
    if exists(oracle_dir):
        shutil.rmtree(oracle_dir)

    cr = ChromeRegression(input_version_pair, oracle_dir, num_of_threads)
    cr.process()

    print (cr.experiment_result)
    print (finder.experiment_result)

if __name__ == "__main__":
    main()
