# Import the Canvas class
from canvas_helpers import file_to_string
from canvasapi import Canvas
from glob import glob
from joblib import Parallel, delayed
import argparse
import multiprocessing
import numpy as np
import progressbar as Pbar
import re

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--parallel",
                    help="grade submissions in parallel",
                    action='store_true')
parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
parser.add_argument("-a", "--all",
                    help="Grade all students again",
                    action='store_true')

args = parser.parse_args()

def print_dict(d):
    max_key = len(max(d.keys(), key=len))
    for k, v in d.items():
        print(k.ljust(max_key) + ': ' + str(v))
    print()


def grade_submission(sub, assignments, args):
    scores_to_complete = {
        'Week1-2': 43,
        'Week3-4': 43,
        'Week5-6': 45,
        'Week7-8': 75}

    # Get assignment- and file name
    assignment_name = sub.split('/')[0]
    handin_name = sub.split('/')[-2]

    # get points and user id
    points = np.loadtxt(glob(sub + handin_name + '_points.txt')[0]).sum()
    user_id = re.findall(r'\d+', handin_name)[0]

    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id)

    # Grade accordingly
    out_str = 'Checking: ' + sub
    if args.all:
        elif (points >= scores_to_complete[assignment_name])
            submission.edit(submission={'posted_grade': 'complete'})
            if args.verbose:
                print(out_str)
                print("Completed with points:", points)
                print()
        elif (points < scores_to_complete[assignment_name])
            submission.edit(submission={'posted_grade': 'incomplete'})
            if args.verbose:
                print(out_str)
                print("Incomplete with points:", points)
                print()
    else:
        if submission.grade == 'complete':
            if args.verbose:
                print(out_str)
                print("Already passed!")
                print()
        elif (points >= scores_to_complete[assignment_name] and
              submission.grade != 'complete'):
            submission.edit(submission={'posted_grade': 'complete'})
            if args.verbose:
                print(out_str)
                print("Completed with points:", points)
                print()
        elif (points < scores_to_complete[assignment_name] and
              submission.grade != 'incomplete' and
              submission.grade != 'complete'):
            submission.edit(submission={'posted_grade': 'incomplete'})
            if args.verbose:
                print(out_str)
                print("Incomplete with points:", points)
                print()


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
reports = sorted(glob('Week*/submissions/*/'))

# Let's start grading!
pbar = Pbar.ProgressBar(redirect_stdout=True)
num_cores = multiprocessing.cpu_count()

if args.parallel:
    if args.verbose:
        print("Grading in parallel!")
    Parallel(n_jobs=num_cores)(delayed(
        grade_submission)(rep, assignments_as_dict, args)
                               for rep in pbar(reports))
else:
    for rep in pbar(reports):
        grade_submission(rep, assignments_as_dict, args)
