import shutil
import argparse

from random import seed

from modules import Preprocesser
from modules import FirefoxRegression
from modules import ChromeRegression

from os.path import join, exists, dirname, basename

def main():
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-b', '--base', required=True, type=int, help='milestone')
    parser.add_argument('-t', '--target', required=True, type=int, help='milestone')
    parser.add_argument('-f', '--firefox', required=True, type=int, help='firefox commit')
    parser.add_argument('-a', '--answer', required=True, type=int, help='firefox commit')
    parser.add_argument('-i', '--input', required=False, type=str, default='', help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=1, help='number of threads')
    parser.add_argument('--baseline', action='store_true')

    args = parser.parse_args()

    seed(0)

    min_dir = join(args.output, 'Minimizer')
    if not exists(min_dir):
        Preprocesser(args.input, args.output, args.job, args.base, args.target).process()

    new_input_dir = min_dir
    finder_dir = join(dirname(args.output), basename(args.output) + '_test')
    if exists(finder_dir):
        shutil.rmtree(finder_dir)
    fd = FirefoxRegression(new_input_dir, finder_dir, args.job,
                           args.base, args.target, args.firefox)
    fd.skip_minimizer()
    fd.process()
    fd.answer(args.answer)


    oracle_dir = join(dirname(args.output), basename(args.output) + '_oracle')
    if exists(oracle_dir):
        shutil.rmtree(oracle_dir)

    if args.baseline:
        cr = ChromeRegression(new_input_dir, oracle_dir, args.job,
                            args.base, args.target, args.answer)
        cr.skip_minimizer()
        cr.process()
        print (cr.experiment_result)
    print (fd.experiment_result)

if __name__ == "__main__":
    main()
