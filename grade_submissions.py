# Import the Canvas class
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
args = parser.parse_args()


def file_to_string(file_name):
    with open(file_name) as f:
        content = f.read()
    return content.strip()


def grade_submission(sub):
    global args
    scores_to_complete = {
        'Week1-2': 43,
        'Week3-4': 50,
        'Week5-6': 50,
        'Week7-8': 50}
    # Get assignment- and file name
    assignment_name = sub.split('/')[0]
    fname = sub.split('/')[-2]

    # get points and user id
    points = np.loadtxt(glob(sub + fname + '_points.txt')[0]).sum()
    user_id = re.findall(r'\d+', fname)[0]

    # Get submission for user
    submission = assignment.get_submission(user_id)

    # Grade accordingly

    out_str = 'Checking: ' + sub
    if submission.grade == 'complete':
        if args.verbose:
            print(out_str)
            print("Already passed!")
            print()
    elif (points >= scores_to_complete[assignment_name] and
          submission.grade != 'complete'):
        if args.verbose:
            print(out_str)
            print("Completed with points:", points)
            print()
        submission.edit(submission={'posted_grade': 'complete'})
    elif (points < scores_to_complete[assignment_name] and
          submission.grade != 'incomplete' and
          submission.grade != 'complete'):
        if args.verbose:
            print(out_str)
            print("Incomplete with points:", points)
            print()
        # submission.edit(submission={'posted_grade': 'incomplete'})


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

# get users assignment and local points
users = course.get_users()
assignment = course.get_assignments()[0]
reports = sorted(glob('Week*/submissions/*/'))

# Let's start grading!
pbar = Pbar.ProgressBar(redirect_stdout=True)
num_cores = multiprocessing.cpu_count()
if args.parallel:
    if args.verbose:
        print("Grading in parallel!")
    Parallel(n_jobs=num_cores)(delayed(
        grade_submission)(rep) for rep in pbar(reports))
else:
    for rep in pbar(reports):
        grade_submission(rep)
