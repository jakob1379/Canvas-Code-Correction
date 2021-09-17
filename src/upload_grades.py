# Import the Canvas class
import argparse
import configparser
import os
import re
import sys
from glob import glob
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np

import progressbar as Pbar
from canvas_helpers import bcolors
from canvas_helpers import file_to_string
from canvas_helpers import init_canvas_course
from p_tqdm import p_map

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

if os.path.join('submissions', '*', '') not in args.path:
    args.path = os.path.join(args.path, 'submissions', '*', '')
if not glob(args.path):
    print("No assignments found in:", args.path)
    sys.exit()


def get_grade(points, assignment):
    """ convert points to grading according to setup in config.ini

    :param points: number of points scores
    :param assignmentName: name of the assignment graded
    :returns: grade
    :rtype: str or float

    """
    points_needed = config.getfloat('scores_to_complete', assignment.name)
    if config.getboolean('DEFAULT', "upload_score"):
        grade = float(points)
        if assignment.grading_type == "percent":
            grade = f"{grade/points_needed * 100:0.0f}%"
    else:
        grade = 'complete' if points >= points_needed else 'incomplete'
    return grade


def grade_submission(sub, assignment):
    """

    :param sub: path to corrected folders
    :param assignments: dictionary with assignment names as keys and canvas assignment objects as values

    """

    if args.verbose:
        out_str = 'Grading: Checking ' + sub
        print(out_str)

    # Get assignment- and file name
    assignment_name = sub.split(os.sep)[0]
    handin_name = sub.split(os.sep)[-2]

    # get points and user id
    fname = os.path.join(sub, handin_name + '_points.txt')
    if not Path(fname).exists():
        print(bcolors.WARNING + "FILE DOES NOT EXIST: " + bcolors.ENDC, fname)
        return

    # Read and sum points in file
    points = round(np.loadtxt(glob(fname)[0]).sum(), 2)
    user_id = re.findall(r'_(\d+)_', handin_name)[0]

    # Get submission for user
    submission = assignment.get_submission(user_id)
    current_grade = submission.grade
    new_grade = get_grade(points, assignment)

    # Grade accordingly
    ans = ''

    if (not args.grade_all) and submission.grade_matches_current_submission and (
            submission.grade is not None) and (current_grade == new_grade):
        if args.verbose:
            print(f"{bcolors.WARNING}Grading: Submission already graded{bcolors.ENDC}\n")
            return

    #  %% Print question and retrieve answer
    points_needed = config.getfloat('scores_to_complete', assignment_name)
    if args.question and not args.parallel:
        if int(points - points_needed) < 0:
            scoreColor = bcolors.FAIL
        else:
            scoreColor = bcolors.OKBLUE

        print(30*'-')
        print(file_to_string(os.path.join(sub, handin_name + '.txt')))

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

    submission.edit(submission={'posted_grade': new_grade})


def main():
    if args.verbose:
        print('Initialising canvas...')

    # Initialize a new Canvas course object
    course = init_canvas_course(config)

    # assignments_as_dict = {ass.name.capitalize().replace(' ', ''): ass
    #                        for ass in course.get_assignments()}
    assignments_as_dict = {ass.name: ass
                           for ass in course.get_assignments()}

    # get users and local points
    reports = sorted(glob(args.path))

    if not reports:
        print("No reports found...")
        sys.exit()

    # Create a list ofcorresponding canvas assignment objects
    assignment_for_reports = [
        assignments_as_dict[rep.split(os.sep)[0]] for rep in reports]

    # Let's start grading!
    if args.parallel:
        if args.verbose:
            print("Grading: runnning in parallel!")
        p_map(grade_submission,
              reports,
              assignment_for_reports,
              num_cpus=args.num_cpus)
    else:
        pbar = Pbar.ProgressBar(redirect_stdout=not args.question)
        for rep, assignment in pbar(zip(reports, assignment_for_reports)):
            grade_submission(rep, assignment)


if __name__ == '__main__':
    main()
