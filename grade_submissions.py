# Import the Canvas class
import argparse
import os
import re
from functools import partial
from glob import glob
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
import progressbar as Pbar
from canvasapi import Canvas
from p_tqdm import p_map

from canvas_helpers import bcolors
from canvas_helpers import file_to_string

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


def get_grade(points, assignmentName):
    """
    funtion that return points or complete/incomplete depending on config
    """
    if config.getboolean('DEFAULT', "upload_score"):
        grade = points
    else:
        points_needed = config.getfloat('scores_to_complete', assignmentName)
        grade = 'complete' if points >= points_needed else 'incomplete'
    return grade


def grade_submission(sub, assignments):
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

    # Read and sum points in file
    points = round(np.loadtxt(glob(fname)[0]).sum(), 2)
    user_id = re.findall(r'_(\d+)_', handin_name)[0]

    # Get submission for user
    assignment = assignments[assignment_name]
    submission = assignment.get_submission(user_id)
    current_grade = submission.grade
    new_grade = get_grade(points, assignment_name)

    # Grade accordingly
    ans = ''

    if (not args.grade_all) and submission.grade_matches_current_submission and (
            submission.grade is not None):
        if args.verbose:
            print(f"{bcolors.WARNING}Grading: Submission already graded{bcolors.ENDC}\n")
            return

    #  %% Print question and retrieve answer
    points_needed = config.getfloat('scores_to_complete', assignment_name)
    if args.question:
        if int(points - points_needed) < 0:
            scoreColor = bcolors.FAIL
        else:
            scoreColor = bcolors.OKBLUE

        print(30*'-')
        print(file_to_string(sub + handin_name + '.txt'))

        print(f"\nPoints in file: {scoreColor}{points}{bcolors.ENDC}/{points_needed}")

        color = bcolors.OKBLUE if current_grade == 'complete' else bcolors.FAIL
        print(f"Current grade: {color}{current_grade}{bcolors.ENDC}")
        print(f"New grade: {bcolors.WARNING}{new_grade}{bcolors.ENDC}")

        ans = str(input("Grade the student?: [y/N]: ") or 'n').lower()
        if ans == 'n':
            if args.verbose:
                print("Submission not graded\n")
            return

    if args.dry:
        return

    # Edit online grade based on scoreColor and/or question answer if any
    if (points >= points_needed or ans == 'o'):
        if args.verbose:
            state = f"{bcolors.OKBLUE}Completed{bcolors.ENDC}"
            print(f"{state} with points: {points}\n")
        grade = 'complete'
    elif (points < points_needed or ans == 'o'):
        if args.verbose:
            state = f"{bcolors.FAIL}Incomplete{bcolors.ENDC}"
            print(f"{state} with {points}: points\n")
        grade = 'incomplete'

    submission.edit(submission={'posted_grade': grade})


def main():
    if args.verbose:
        print('Initialising canvas...')

    # Initialize a new Canvas object
    canvas = Canvas(config['DEFAULT']['apiurl'], config['DEFAULT']['token'])

    # init course
    course_id = config.get('DEFAULT', 'courseid')
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
        p_map(partial(grade_submission, assignments=assignments_as_dict),
              reports, num_cpus=args.num_cpus)
    else:
        pbar = Pbar.ProgressBar(redirect_stdout=not args.question)
        for rep in pbar(reports):
            grade_submission(rep, assignments_as_dict)


if __name__ == '__main__':
    main()
