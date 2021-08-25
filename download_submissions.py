# Import the Canvas class
import argparse
import multiprocessing
import os
import shutil
import sys
from functools import partial
from glob import glob
from pathlib import Path

import progressbar as Pbar
from canvasapi import Canvas
from p_tqdm import p_umap
from canvas_helpers import create_file_name
from canvas_helpers import download_url
from canvas_helpers import extract_comment_filenames

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

# init course
if not config.get('DEFAULT', 'courseid'):
    print("No courseid found in config!")
    sys.exit(2)
elif not config.get('DEFAULT', 'token'):
    print("No token found in config!")
    sys.exit(2)

# Initialize a new Canvas object
token = config.get('DEFAULT', 'token')
url = config.get('DEFAULT', 'apiurl')
canvas = Canvas(url, token)

# create course object
course_id = config.get('DEFAULT', 'courseid')
course = canvas.get_course(course_id)

# set up argparse
parser = argparse.ArgumentParser("""
Tool to download assignments.
Default behaviour is to only download handins that have been changed""")
parser.add_argument("-v", "--verbose",
                    help="sets verbosity",
                    action='store_true')
parser.add_argument("-p", "--parallel",
                    help="download in parallel",
                    action='store_true')
parser.add_argument("-n", "--num-cores",
                    help="description",
                    metavar="num-cores",
                    type=int,
                    nargs='?',
                    default=multiprocessing.cpu_count())
parser.add_argument("-a", "--assignment",
                    help="Specific assignments to download",
                    metavar="assignement",
                    default=[a.name for a in course.get_assignments()],
                    nargs='*',
                    choices=[a.name for a in course.get_assignments()],
                    type=str)
parser.add_argument("-s", "--student-id",
                    help="Specific student-id to download",
                    metavar="student-id",
                    nargs='*',
                    type=int)
parser.add_argument("-d", "--download",
                    help="Which handins to download",
                    dest='download',
                    type=str,
                    # nargs='?',
                    default="new",
                    choices=["failed", "uncommented", "all", "new"])
parser.add_argument("-l", "--list-assignments",
                    help="list assignments for course and exit",
                    action='store_true')
parser.add_argument("--dry",
                    help="dry run where nothing is downloaded",
                    action='store_true')

args = parser.parse_args()

if args.list_assignments:
    print("Possible assignments are:")
    print('\n'.join([' - '+a.name for a in course.get_assignments()]))
    sys.exit()


def download_submission(sub, old_files):
    try:
        url = sub.attachments[0]['url']
        if url:
            file_name = create_file_name(sub, course)
            assignment_name = course.get_assignment(sub.assignment_id).name
            # assignment_name = assignment_name.replace(' ', '') # not necessary, but nice for more compact naming.
            directory = os.path.join(assignment_name, 'submissions', '')
            Path(directory).mkdir(parents=True, exist_ok=True)

            # check if user has old submissions
            folders_to_remove = [old for old in old_files
                                 if str(sub.user_id) in old and
                                 os.path.join(file_name, '') not in old]
            for f in folders_to_remove:
                shutil.rmtree(f, ignore_errors=True)
            # download attachment if it doesn't exist,
            if os.path.join(directory, file_name, '') not in old_files:
                url = sub.attachments[0]['url']
                if args.verbose:
                    print("Saving to:", directory+file_name+'.zip')
                if not args.dry:
                    download_url(url, directory+file_name+'.zip')

    except AttributeError:
        if args.verbose:
            print("Submission has no attachment:", sub.id)


def find_submissions(args):
    # Walk through all assignments and find submissions
    submissions = []
    sub_len = 0
    count = 0

    for assignment in [a for a in course.get_assignments() if a.name in args.assignment]:
        if args.verbose:
            print("Checking " + assignment.name + "...")
        if args.download == "all":
            submissions += list(assignment.get_submissions())
        elif args.download == "failed":
            submissions += [sub for sub in assignment.get_submissions()
                            if sub.grade == 'incomplete']
        elif args.download == "uncommented":
            for sub in assignment.get_submissions(include='submission_comments'):
                comment_files = extract_comment_filenames(
                    sub.submission_comments)
                submission_fname = create_file_name(sub, course) + '.zip'
                if submission_fname not in comment_files:
                    submissions.append(sub)
        elif args.download == "new":
            for sub in assignment.get_submissions():
                if (vars(sub).get('attachments') is not None and
                        (not sub.grade_matches_current_submission or sub.grade is None)):
                    submissions.append(sub)

    # if specific students where chosen filter them
    if args.student_id:
        submissions = [sub for sub in submissions if sub.user_id in args.student_id]
    if args.verbose:
        print("found:", len(submissions)-sub_len)
        sub_len = len(submissions)

    return submissions


def main():
    old_files = glob(os.path.join("*", 'submissions', '*', ''))
    submissions = find_submissions(args)
    print("Submissions to correct:", len(submissions))

    # Download submissions
    if submissions:
        if args.parallel:
            print("Downloading submissions in parallel!")
            p_umap(
                partial(download_submission, old_files=old_files),
                submissions,
                num_cpus=args.num_cores)
        else:
            pbar = Pbar.ProgressBar(redirect_stdout=True)
            for sub in pbar(submissions):
                download_submission(sub, old_files)
    else:
        print("No submissions to download...")


if __name__ == '__main__':
    main()
