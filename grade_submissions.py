# Import the Canvas class
from canvas_helpers import file_to_string, bcolors, flatten_list
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
parser.add_argument("-a", "--grade-all",
                    help="Grade all students again",
                    action='store_true')
parser.add_argument("-q", "--question",
                    help="question what grade to give",
                    action='store_true')
parser.add_argument("path", nargs='?', default='Week*/submissions/*/',
                    help="Path to check")
args = parser.parse_args()

if '/submissions/*/' not in args.path:
    args.path += '/submissions/*/'


def grade_submission(sub, assignments, args):
    out_str = 'Grading: Checking ' + sub
    if args.verbose:
        print(out_str)

    scores_to_complete = {
        'Week1-2': 43,
        'Week3-4': 43,
        'Week5-6': 67.5,
        'Week7-8': 2}

    # Get assignment- and file name
    assignment_name = sub.split('/')[0]
    handin_name = sub.split('/')[-2]

    # get points and user id
    points = round(
        np.loadtxt(glob(sub + handin_name + '_points.txt')[0]).sum(), 2)
    user_id = re.findall(r'\d+', handin_name)[0]

    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id)
    current_grade = submission.grade

    # Grade accordingly
    ans = ''

    if not args.grade_all and submission.grade_matches_current_submission and (
            submission.grade is not None):
        if args.verbose:
            print("Grading: Submission already graded\n")
        return

    #  %% Print question and retrieve answer
    if args.question:
        score = round(points - scores_to_complete[assignment_name])
        if score < 0:
            score = bcolors.FAIL+str(score)
        else:
            score = bcolors.OKBLUE+str(score)

        print(30*'-')
        print(file_to_string(sub + handin_name + '.txt'))
        print("\nPoints in file:",
              str(points)+'-'+str(scores_to_complete[assignment_name]),
              "=", score + bcolors.ENDC)
        print("\nPoints to complete", assignment_name+':',
              scores_to_complete[assignment_name])
        print("Current grade:", current_grade)
        ans = str(input("Grade the student?: [y/N]: ") or 'n').lower()
        if ans == 'n':
            if args.verbose:
                print("Submission not graded\n")
            return

    # %% Edit online grade based on score and/or question answer if any
    if points >= scores_to_complete[assignment_name] or ans == 'o':
        submission.edit(submission={'posted_grade': 'complete'})
        if args.verbose:
            print("Completed with points:", points)
    elif points < scores_to_complete[assignment_name] or ans == 'o':
        submission.edit(submission={'posted_grade': 'incomplete'})
        if args.verbose:
            print("Incomplete with points:", points)
    if args.verbose:
        print()


# %% Init
if __name__ == '__main__':
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
    reports = [rep for rep in sorted(glob(args.path))]


    # Let's start grading!
    # pbar = Pbar.ProgressBar(redirect_stdout=True)
    num_cores = multiprocessing.cpu_count()

    if args.parallel:
        if args.verbose:
            print("Grading: runnning in parallel!")
            Parallel(n_jobs=num_cores)(delayed(
                grade_submission)(rep, assignments_as_dict, args)
                                       for rep in reports)
    else:
        for rep in reports:
            grade_submission(rep, assignments_as_dict, args)
