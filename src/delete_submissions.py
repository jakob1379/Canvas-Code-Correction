import argparse
import os
import shutil
from glob import glob
from multiprocessing import cpu_count

from p_tqdm import p_map


def setup():
    choices = sorted([i.split(os.sep)[0] for i in glob('*/submissions/')])
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--parallel",
                        help="Set number of cores for parallel execution. Set cores to 1 for sequential",
                        metavar="num cores",
                        type=int,
                        nargs='?',
                        default=cpu_count())
    parser.add_argument("assignments",
                        help="Select assignments to unzip submissions within. Multiple may be selected and/or usage of wildcards for assignment names only",
                        metavar="assignments",
                        nargs='*',
                        default=choices)
    return parser.parse_args()


def find_files(assignments):
    files = []
    # Find files
    for assignment in assignments:
        tmp_files = glob(os.path.join(assignment, "submissions", "*"))
        if tmp_files:
            files += tmp_files
    return files


def rmfiles(files):
    p_map(shutil.rmtree, files)


def main():
    args = setup()
    files = find_files(args.assignments)
    rmfiles(files)


if __name__ == '__main__':
    main()
