# Import the Canvas class
from canvas_helpers import (file_to_string, create_file_name,
                            flatten_list, print_dict, bcolors)
from canvasapi import Canvas
from glob import glob
from joblib import Parallel, delayed
import argparse
import multiprocessing
import re
from urllib.parse import unquote
from tabulate import tabulate

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--parallel",
                    help="grade submissions in parallel",
                    action='store_true')
parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
parser.add_argument("-q", "--question",
                    help="prompt if a non-matching comment should be uploaded",
                    action='store_true')
parser.add_argument("-a", "--all",
                    help="description",
                    action='store_true')
parser.add_argument("path", nargs='?', default='Week*/submissions/*/',
                    help="Path to check")
args = parser.parse_args()
if '/submissions/*/' not in args.path:
    args.path += '/submissions/*/'


def extract_comment_filenames(comments):
    # Get all attachments in comments as one flat list
    return flatten_list(
        [[unquote(att.get('filename')) for att in comm.get('attachments')
          if att.get('filename')]
         for comm in comments if comm.get('attachments')])


def upload_comments(sub, assignments, args):
    if args.verbose:
        out_str = 'Checking: ' + sub
        print(out_str)
    # Get assignment- and file name
    assignment_name = sub.split('/')[0]
    txt_name = sub.split('/')[-2]
    handin_name = re.sub(" ", "+", txt_name)

    # get points and user id
    user_id = re.findall(r'\d+', handin_name)[0]
    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id,
                                           include='submission_comments')

    # extract attached filenames from comments
    comment_files = extract_comment_filenames(submission.submission_comments)

    # get path to comment zip
    file_to_upload = glob(sub + '*.zip')

    if file_to_upload:
        file_to_upload = file_to_upload[0]
        upload_name = file_to_upload.split('/')[-1]
    else:
        out_str = (
            bcolors.WARNING + "zip to upload not found in: ".upper() + sub +
            bcolors.ENDC)
        print(out_str)
        return

    # Only upload if it isn't already there.
    if handin_name+'.zip' not in comment_files or args.all:
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
                    showindex='always'),'\n')
            else:
                print(None)
            print("\nNew comment:\n", upload_name, '\n', handin_name+'.zip\n')
            ans = input("Upload: Should new comment be uploaded? [y/N] ")
        if ans.lower() == 'y' or not args.question:
            if args.verbose or args.question:
                print("Upload: Comment has been uploaded!\n")
            # submission.upload_comment(file_to_upload)
        elif args.question:
            print("Upload: Comments NOT uploaded.")
    elif args.verbose:
        print("Upload: feedback already uploaded\n")


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
reports = [rep for rep in sorted(glob(args.path)) if 'Week7-8' not in rep]

# Let's start grading!
num_cores = multiprocessing.cpu_count()


if args.parallel:
    if args.verbose:
        print("Uploading comments in parallel!")
    Parallel(n_jobs=num_cores)(delayed(
        upload_comments)(rep, assignments_as_dict, args) for
                               rep in reports)
else:
    for rep in reports:
        upload_comments(rep, assignments_as_dict, args)
