# Import the Canvas class
import argparse
import configparser
import os
import re
import sys
from glob import glob
from multiprocessing import cpu_count

import progressbar as Pbar
from canvas_helpers import bcolors
from canvas_helpers import download_url
from canvas_helpers import extract_comment_filenames
from canvas_helpers import file_to_string
from canvas_helpers import init_canvas_course
from canvas_helpers import md5sum
from p_tqdm import p_map
from tabulate import tabulate

config = configparser.ConfigParser()
config.read('config.ini')

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--parallel",
                    help="grade submissions in parallel",
                    action='store_true')
parser.add_argument("-n", "--num-cpus",
                    help="description",
                    metavar="num-cpus",
                    type=int,
                    nargs='?',
                    default=cpu_count())
parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
parser.add_argument("-q", "--question",
                    help="prompt if a non-matching comment should be uploaded",
                    action='store_true')
parser.add_argument("-a", "--all",
                    help="upload all feedback RISK OF DUPLICATES ON ABSALON",
                    action='store_true')
parser.add_argument("-d", "--dry",
                    help="dry run without uploading anything",
                    action='store_true')
parser.add_argument("path", nargs='?',
                    default=os.path.join('*', 'submissions', '*', ''),
                    help="Path to check")
args = parser.parse_args()

if os.path.join('submissions', '*', '') not in args.path:
    args.path = os.path.join(args.path, 'submissions', '*', '')
if not glob(args.path):
    print("No assignments found in:", args.path)
    sys.exit()


def upload_comments(sub, assignment):
    """ uploads zipped content to absalone if it is not already there. Compared with md5sum.

    :param sub: Path to submission folder
    :param assignments: dict of assignment names as key and canvas assignment object as values
    # TODO: change to just take the canvas object instead of the whole dict

    """

    if not glob(f"{sub}*.zip"):
        return

    if args.verbose:
        out_str = 'Checking: ' + sub
        print(out_str)

    # Get assignment- and file name
    txt_name = sub.split(os.sep)[-2]
    handin_name = re.sub(" ", "+", txt_name)

    # get points and user id
    user_id = re.findall(r'_(\d+)_', handin_name)[0]

    # Get submission for user
    submission = assignment.get_submission(user_id,
                                           include='submission_comments')

    # extract attached filenames from comments
    comment_files = extract_comment_filenames(submission.submission_comments)

    # get path to comment zip
    file_to_upload = glob(sub + '*.zip')

    # Compare latest online comment with local comment
    fname = ""
    new_md5 = md5sum(file_to_upload[0])
    if submission.submission_comments:
        try:
            latest_comment_url = submission.submission_comments[-1]['attachments'][0]['url']
            fname = submission.submission_comments[-1]['attachments'][0]['display_name']
            download_url(
                latest_comment_url,
                os.path.join('tmp', fname))
            previous_md5 = md5sum(os.path.join('tmp', fname))
        except KeyError or FileNotFoundError:
            previous_md5 = ""
    else:
        previous_md5 = ""

    if file_to_upload:
        file_to_upload = file_to_upload[0]
        upload_name = file_to_upload.split(os.sep)[-1]
    else:
        out_str = (
            bcolors.WARNING + "zip to upload not found in: ".upper() + sub +
            bcolors.ENDC)
        print(out_str)
        return

    # Only upload if it isn't already there.
    # or (previous_md5 != new_md5):
    if (handin_name+'.zip' not in comment_files) or (previous_md5 != new_md5) or args.all:
        if args.verbose:
            print("Upload: uploading feedback\n", file_to_upload)

        ans = ''
        if args.question:
            print(30*'-')
            print(file_to_string(sub + txt_name + '.txt'))
            print("\nOld Feedback uploads:")
            if comment_files:
                print(tabulate(
                    [[i] for i in comment_files],
                    headers=['Comment names'],
                    showindex='always'), '\n')
            else:
                print(None)
            print(f"Old comment:   {fname}\n")
            print(f"New comment:   {upload_name}")

            if previous_md5 == new_md5:
                md5string = f"{bcolors.OKBLUE}Yes{bcolors.ENDC}"
            else:
                md5string = f"{bcolors.FAIL}No{bcolors.ENDC}"
            print("md5sum are equal:", md5string)

            while ans not in {'y', 'n'}:
                ans = (input("Upload: Should new comment be uploaded? [y/N] ")
                       or 'n').lower()

        if ans.lower() == 'y' or not args.question:
            if not args.dry:
                submission.upload_comment(file_to_upload)
                if args.verbose or args.question:
                    comment = bcolors.OKBLUE + "Upload: Comment has been uploaded!\n"
        elif args.question or args.verbose:
            comment = bcolors.FAIL + "Upload: Comments NOT uploaded.\n"
    elif args.verbose:
        comment = bcolors.WARNING + "Upload: feedback already uploaded\n"
    if args.verbose:
        print(comment + bcolors.ENDC)


def main():
    # %% Init
    if args.verbose:
        print('Initialising canvas...')

    # Initialize a new Canvas course object
    course = init_canvas_course(config)

    assignments_as_dict = {ass.name: ass
                           for ass in course.get_assignments()}
    # get local submissions
    reports = sorted(glob(args.path))

    if not reports:
        print("No reports found...")
        sys.exit()

    # Create a list ofcorresponding canvas assignment objects
    assignment_for_reports = [
        assignments_as_dict[reports[0].split(os.sep)[0]] for rep in reports]

    # Let's start grading!
    if args.parallel:
        if args.verbose:
            print("Uploading comments in parallel!")

            p_map(
                upload_comments,
                reports,
                assignment_for_reports,
                num_cpus=args.num_cpus)
    else:
        pbar = Pbar.ProgressBar(redirect_stdout=not args.question)
        for rep, assignment in pbar(zip(reports, assignment_for_reports)):
            upload_comments(rep, assignment)

    # clear temporary files
    files = glob(os.path.join("tmp", "*"))
    for fname in files:
        os.remove(fname)


if __name__ == '__main__':
    main()
