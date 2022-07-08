import argparse

from random import seed

from modules import Preprocesser
from modules import FirefoxRegression

from os.path import join, dirname, basename

def main():
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-i', '--input', required=False, type=str, default='', help='input directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='output directory')
    parser.add_argument('-j', '--job', required=False, type=int, default=1, help='number of threads')
    parser.add_argument('-b', '--base', required=True, type=int, help='milestone')
    parser.add_argument('-t', '--target', required=True, type=int, help='milestone')
    parser.add_argument('-f', '--firefox', required=True, type=int, help='firefox commit')
    args = parser.parse_args()

    seed(0)
    Preprocesser(args.input, args.output, args.job,
                 args.base, args.target).process()

    new_input_dir = join(args.output, 'Minimizer')
    new_output_dir = join(dirname(args.output), basename(args.output) + '_r2z2')
    FirefoxRegression(new_input_dir, new_output_dir, args.job,
                      args.base, args.target, args.firefox).process()


if __name__ == "__main__":
    main()
