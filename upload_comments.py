# Import the Canvas class
import argparse
import multiprocessing
import os
import re
from glob import glob
from p_tqdm import p_map
from functools import partial
from joblib import Parallel
from joblib import delayed
import shutil
from canvas_helpers import bcolors
from canvas_helpers import download_url
from canvas_helpers import extract_comment_filenames
from canvas_helpers import file_to_string
from canvas_helpers import md5sum
from canvasapi import Canvas
from tabulate import tabulate
from multiprocessing import cpu_count
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
parser.add_argument("path", nargs='?',
                    default=os.path.join('*', 'submissions', '*', ''),
                    help="Path to check")
parser.add_argument("-d", "--dry",
                    help="dry run without uploading anything",
                    action='store_true')
args = parser.parse_args()


def upload_comments(sub, assignments, args):
    if args.verbose:
        out_str = 'Checking: ' + sub
        print(out_str)

    # Get assignment- and file name
    assignment_name = sub.split(os.sep)[0]
    txt_name = sub.split(os.sep)[-2]
    handin_name = re.sub(" ", "+", txt_name)

    # get points and user id
    user_id = re.findall(r'_(\d+)_', handin_name)[0]
    # Get submission for user
    assignment = assignments[assignment_name]
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
            download_url(latest_comment_url, 'tmp/' + fname)
            previous_md5 = md5sum('tmp/' + fname)
        except KeyError or FileNotFoundError:
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
    if (handin_name+'.zip' not in comment_files) or args.all:
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
            print("New comment:   ", upload_name)
            print("Old comment:   ", fname, '\n')

            if previous_md5 == new_md5:
                md5string = bcolors.OKBLUE + "Yes" + bcolors.ENDC
            else:
                md5string = bcolors.FAIL + "No" + bcolors.ENDC
            print("md5sum are equal:", md5string)

            ans = input("Upload: Should new comment be uploaded? [y/N] ")

        if ans.lower() == 'y' or not args.question:
            if args.verbose or args.question:
                print(bcolors.OKBLUE + "Upload: Comment has been uploaded!\n" + bcolors.ENDC)
            if not args.dry:
                submission.upload_comment(file_to_upload)
        elif args.question:
            print(bcolors.FAIL + "Upload: Comments NOT uploaded." + bcolors.ENDC)
    elif args.verbose:
        print(bcolors.WARNING + "Upload: feedback already uploaded\n" + bcolors.ENDC)


# %% Init
if args.verbose:
    print('Initialising canvas...')

# Canvas API URL
domain = 'absalon.ku.dk'
API_URL = "https://"+domain+"/"

# Canvas API key
API_KEY = file_to_string('token')

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

# init course
course_id = file_to_string('course_id')
course = canvas.get_course(course_id)
assignments_as_dict = {ass.name.capitalize().replace(' ', ''): ass
                       for ass in course.get_assignments()}

# get users and local points
users = course.get_users()
reports = sorted(glob(args.path))

# Let's start grading!
num_cores = multiprocessing.cpu_count()


if args.parallel:
    if args.verbose:
        print("Uploading comments in parallel!")
    p_map(
        partial(upload_comments, assignments=assignments_as_dict, args=args),
        reports,
        num_cpus=args.num_cpus)
else:
    for rep in reports:
        upload_comments(rep, assignments_as_dict, args)

# clear temporary files
files = glob("tmp/*")
for fname in files:
    os.remove(fname)
