import argparse
import os
import shutil
from glob import glob
from multiprocessing import cpu_count
from pathlib import Path

from p_tqdm import p_map


def setup():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("assignments",
                        help="Select assignments to unzip submissions within. Multiple may be selected and/or usage of wildcards for assignment names only",
                        metavar="assignments",
                        nargs='*',
                        default=sorted([i.split(os.sep)[0]
                                        for i in glob('*/submissions/')]),
                        type=str)
    parser.add_argument("-p", "--parallel",
                        help="Set number of cores for parallel execution. Set cores to 1 for sequential",
                        metavar="parallel",
                        type=int,
                        nargs='?',
                        default=cpu_count())

    return parser.parse_args()


def unzip(zipfile):
    file = Path(zipfile)
    sub_name = file.resolve().parent

    # Unpack zipfile
    try:
        shutil.unpack_archive(zipfile, sub_name)
    except shutil.ReadError:
        return

    # Remove __MACOSX and the original zip-file
    for path in sub_name.rglob("__MACOSX"):
        shutil.rmtree(path, ignore_errors=True)
    file.unlink(missing_ok=True)

    # If content is packed as a single folder - move files one up
    subfiles = list(sub_name.glob('*'))
    if len(subfiles) == 1:
        subfolder = subfiles[0]
        if not subfolder.is_dir():
            return
        # needed to handle nested folders with same name
        subfolder = subfolder.rename(str(subfolder) + "-old")
        shutil.copytree(subfolder, subfolder.parents[0], dirs_exist_ok=True)
        shutil.rmtree(subfolder)


def main():
    args = setup()

    # Find files
    files = []
    for assignment in args.assignments:
        tmp_files = glob(os.path.join(assignment, "submissions", "*", "*.zip"))
        if tmp_files:
            files += tmp_files

    if files:
        p_map(unzip, files)
    else:
        print("No files to unzip...")


if __name__ == '__main__':
    main()
