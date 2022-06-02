import argparse

from random import seed
from helper import FileManager

from modules import ChromeRegression

def main():
    parser = argparse.ArgumentParser(description='Usage')
    parser.add_argument('-b', '--base', required=True, type=int, help='milestone')
    parser.add_argument('-t', '--target', required=True, type=int, help='milestone')
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

    # 94 --> after 93 ~ before 95 
    base = bisect.bisect_right(versions, milestone[args.base])
    target = bisect.bisect_left(versions, milestone[args.target])
    answer = bisect.bisect_right(versions, milestone[args.answer])
    
    vers = (versions[base], versions[target], versions[answer])
    output_dir = args.output
    num_of_threads = args.job

    input_version_pair = {}

    for inp in inputs:
      input_version_pair[inp] = vers
    ChromeRegression(input_version_pair, output_dir, num_of_threads).process()

if __name__ == "__main__":
    import time

    start = time.time()
    main()
    end = time.time()
    elapsed = end - start
    from datetime import timedelta
    elapsed_time = str(timedelta(seconds=elapsed))
    print (elapsed_time)
