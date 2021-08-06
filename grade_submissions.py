# Import the Canvas class
import argparse
import multiprocessing
import os
import re
from functools import partial
from glob import glob
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
import progressbar as Pbar
from canvasapi import Canvas
from joblib import Parallel
from joblib import delayed
from math import floor
from p_tqdm import p_map

from canvas_helpers import bcolors
from canvas_helpers import file_to_string
from canvas_helpers import flatten_list

import configparser
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
parser.add_argument("-a", "--grade-all",
                    help="Grade all students again",
                    action='store_true')
parser.add_argument("-q", "--question",
                    help="question what grade to give",
                    action='store_true')
parser.add_argument("path", nargs='?',
                    default=os.path.join('*', 'submissions', '*', ''),
                    help="Path to check")
parser.add_argument("-d", "--dry",
                    help="Dry run. Doesn't change anything",
                    action='store_true')

args = parser.parse_args()


def grade_submission(sub, assignments, args):
    out_str = 'Grading: Checking ' + sub
    if args.verbose:
        print(out_str)

    # Get assignment- and file name
    assignment_name = sub.split(os.sep)[0]
    handin_name = sub.split(os.sep)[-2]

    # get points and user id
    fname = sub + handin_name + '_points.txt'
    if not Path(fname).exists():
        print(bcolors.WARNING + "FILE DOES NOT EXIST: " + bcolors.ENDC, fname)
        return

    points = round(
        np.loadtxt(glob(fname)[0]).sum(), 2)
    user_id = re.findall(r'_(\d+)_', handin_name)[0]

    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id)

    # Grade accordingly
    ans = ''
    if not args.grade_all and submission.grade_matches_current_submission and (
            submission.grade is not None):
        if args.verbose:
            print(bcolors.WARNING + "Grading: Submission already graded\n" + bcolors.ENDC)
        return

    #  %% Print question and retrieve answer
    points_needed = float(config['scores_to_complete'][assignment_name])
    # TODO: CHANGE LOGIC FROM submission.grade == 'complete' to handle if
    # value should be uploaded and there is no longer complete/incomplete but
    # a number
    if args.question:
        score = floor(points - points_needed)
        if score < 0:
            score = bcolors.FAIL
        else:
            score = bcolors.OKBLUE

        print(30*'-')
        print(file_to_string(sub + handin_name + '.txt'))
        print("\nPoints in file:",
              score+str(points)+bcolors.ENDC+'/'+str(points_needed))

        color = bcolors.OKBLUE if submission.grade == 'complete' else bcolors.FAIL
        print("Current grade:", color+submission.grade+bcolors.ENDC)

        while ans not in {'y', 'n'}:
            ans = (input("Grade the student?: [y/N]: ") or 'n').lower()
        if ans == 'n':
            if args.verbose:
                print("Submission not graded\n")
            return

    # %% Edit online grade based on score and/or question answer if any
    if (points >= points_needed or ans == 'o') and (not args.dry):
        if args.verbose:
            print(bcolors.OKBLUE + "Completed" + bcolors.ENDC + " with points:", points)
        if not args.dry:
            submission.edit(submission={'posted_grade': 'complete'})
    elif (points < points_needed or ans == 'o'):
        if args.verbose:
            print(bcolors.FAIL + "Incomplete " + bcolors.ENDC + " with points:", points)
        if not args.dry:
            submission.edit(submission={'posted_grade': 'incomplete'})


def main():
    if args.verbose:
        print('Initialising canvas...')

    # Initialize a new Canvas object
    canvas = Canvas(config['DEFAULT']['apiurl'], config['DEFAULT']['token'])

    # init course
    course_id = config['DEFAULT']['courseid']
    course = canvas.get_course(course_id)
    # assignments_as_dict = {ass.name.capitalize().replace(' ', ''): ass
    #                        for ass in course.get_assignments()}
    assignments_as_dict = {ass.name: ass
                           for ass in course.get_assignments()}

    # get users and local points
    reports = sorted(glob(args.path))

    # Let's start grading!
    if args.parallel:
        if args.verbose:
            print("Grading: runnning in parallel!")
        p_map(partial(grade_submission, assignments=assignments_as_dict,
              args=args), reports, num_cpus=args.num_cpus)
    else:
        redirect_stdout = False if args.question else True
        pbar = Pbar.ProgressBar(redirect_stdout=redirect_stdout)
        for rep in pbar(reports):
            grade_submission(rep, assignments_as_dict, args)


if __name__ == '__main__':
    main()
