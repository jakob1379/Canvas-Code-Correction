# Import the Canvas class
from datetime import datetime
import re
import multiprocessing
import seaborn as sns
from canvas_helpers import (file_to_string,
                            flatten_list)
from canvasapi import Canvas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pandasgui import show
from functools import partial
from p_tqdm import p_map
from tabulate import tabulate
import pandas.plotting as pplot
plt.style.use('ggplot')
# plt.rcParams.update({
#     "text.usetex": True,
#     "font.family": "sans-serif",
#     "font.sans-serif": ["Helvetica"]})

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--show",
                    help="Show resulting plot",
                    action='store_true')
parser.add_argument("-o", "--out",
                    help="outname for resulting image",
                    metavar="out",
                    type=str,
                    nargs='?',
                    default="scores.pdf")
parser.add_argument("-n", "--num-cores",
                    help="Number of cores to use and run in parallel",
                    metavar="parallel",
                    type=int,
                    nargs='?',
                    default=multiprocessing.cpu_count())

parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
args = parser.parse_args()


def student_passed(student, assignments):
    return all([ass.get_submission(student).grade for ass in assignments])


def count_students_passed(course, args):
    students = [student.id for student in course.get_users(enrollment_type=['student'])]

    assignments = course.get_assignments()
    pool = multiprocessing.Pool(processes=args.num_cores)
    students_passed = sum(
        pool.map(partial(student_passed, assignments=assignments), students))

    # normalize
    students_passed /= len(students)
    return students_passed


def plot_scores(df, course, args):
    if args.verbose:
        print("Aggregating data for plotting...")
    plot_data = (
        df
        .groupby(["Assignment", "grade"])
        .apply(lambda group: len(group)/num_students)
        .to_frame("percentage")
        .reset_index()
        .sort_values(by="Assignment"))
    df2 = (
        df[df.grade == "complete"]
        .groupby("Assignment")
        .agg({"attempt": ["mean", "var", "min", "max"]})
        .reset_index()
        .set_index("Assignment")
        .round(2)
    )
    df2.index.name = None
    # Remove unnecessary multindex
    df2.columns = df2.columns.droplevel(0)

    if args.verbose:
        print("Counting students who have passed...")
    # Count how many have passed the course
    students_passed = count_students_passed(course, args)

    if args.verbose:
        print("Plotting...")
    fig, (ax1, ax2) = plt.subplots(
        nrows=1, ncols=2,
        sharex=False, sharey=True,
        figsize=(9, 4)
    )
    ax1 = sns.barplot(data=plot_data, x="percentage",
                      y="Assignment", hue="grade", ax=ax1)
    ax1.axis('tight')

    ax1.axvline(students_passed, linestyle='dashed', color='tab:green',
                label=f'Students Passed: {100*students_passed:.2f}%')

    ax1.set_xlabel('Grade count')
    ax1.set_xlim(0, 1.01)
    ax1.legend(loc="best", framealpha=0.3)

    if df[(df.grade == "complete") & (df.Assignment == "Week 7-8")].empty:
        df = df.append(dict(
            Assignment="Week 7-8",
            grade="complete",
            attempt=0
        ), ignore_index=True)

    sns.violinplot(
        data=df[df.grade == "complete"],
        y="Assignment",
        x="attempt",
        ax=ax2
    )

    sns.stripplot(
        data=df,
        x="attempt",
        y="Assignment",
        jitter=True,
        zorder=1,
        ax=ax2
    )

    ax2.text(0.98, 0.55,
             tabulate(df2, headers=df2.columns),
             horizontalalignment='right',
             verticalalignment='top',
             transform=ax2.transAxes,
             color='black', fontsize=10,
             bbox=dict(boxstyle="square", alpha=0.15))

    ax2.axis('tight')

    fig.suptitle(datetime.now().strftime("%b %d %Y %T"))
    if args.verbose:
        print("Saving figure...")
    fig.tight_layout()

    if args.show:
        plt.show()
    else:
        fig.savefig(args.out, format='pdf')


if __name__ == '__main__':

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
    assignments = course.get_assignments()

    try:
        scores.shape
    except:
        scores = np.array(flatten_list(
            [[(assignment.name, sub.grade, sub.attempt) for sub in assignment.get_submissions()]
             for assignment in assignments]))

    # Count unique values i.e. complete, incomplete and not handed in
    num_students = len(list(course.get_users(type="student")))
    df = pd.DataFrame(scores, columns=['Assignment', 'grade', "attempt"])
    df.loc[df.Assignment == "Week1-2", "Assignment"] = "Week 1-2"
    df.grade.fillna('Not handed in', inplace=True)  # replace nan with not handed in
    df.attempt.fillna(0, inplace=True)  # replace nan with not handed in
    df = (
        df.apply(pd.to_numeric, errors="coerce")
        .fillna(df)
        .reset_index(drop=True)
    )

    plot_scores(df, course, args)
    print("Done!")
