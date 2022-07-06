import shutil
import argparse

from os.path import join, exists
from random import seed
from helper import FileManager, MILESTONE

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
    milestone = MILESTONE

    import bisect

    from pyvirtualdisplay import Display

    disp = Display(size=(1200, 800))
    disp.start()

    base = bisect.bisect_left(versions, milestone[args.base - 1]) - 1
    target = bisect.bisect_left(versions, milestone[args.target - 1]) - 1
    answer = bisect.bisect_left(versions, milestone[args.answer]) - 1
    answer = versions[answer]
    

    vers = (versions[base], versions[target], args.firefox)
    print ('versions:', vers, answer)
    output_dir = args.output
    num_of_threads = args.job

    min_dir = join(output_dir, 'Minimizer')
    print ('min_dir', min_dir)
    if not exists(min_dir):
        cv_dir = join(output_dir, 'CrossVersion')
        if exists(cv_dir): shutil.rmtree(cv_dir)
        input_version_pair = {}
        for inp in inputs:
            input_version_pair[inp] = vers
        Preprocesser(input_version_pair, output_dir, num_of_threads).process()


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
    disp.stop()

if __name__ == "__main__":
    main()
