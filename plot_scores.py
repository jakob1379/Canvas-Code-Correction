from canvas_helpers import file_to_string
from canvasapi import Canvas
from datetime import datetime
from functools import partial
from itertools import chain
from tabulate import tabulate
import argparse
import matplotlib.pyplot as plt
import multiprocessing
import pandas as pd
import progressbar as Pbar
import seaborn as sns
from p_tqdm import p_map
plt.style.use('ggplot')

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
                    metavar="cores",
                    type=int,
                    nargs='?',
                    default=multiprocessing.cpu_count())

parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
args = parser.parse_args()


def count_students_no_handins(course, args):
    students = [student.id for student in course.get_users(enrollment_type=['student'])]

    assignments = course.get_assignments()
    pool = multiprocessing.Pool(processes=args.num_cores)
    students_passed = sum(
        pool.map(partial(student_passed, assignments=assignments), students))

    # normalize
    students_passed /= len(students)
    return students_passed


def plot_scores(df, course, args):
    plot_data = (
        df
        .groupby(["Assignment", "grade"])
        .apply(lambda group: len(group)/df.uid.nunique())
        .to_frame("percentage")
        .reset_index()
        .sort_values(by="Assignment"))
    df2 = (
        df[df.grade == "complete"]
        .groupby("Assignment")
        .agg({"attempts": ["mean", "var", "min", "max"]})
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
    num_students_passed = df.groupby('uid').filter(lambda group: all(
        group.grade == 'complete')).uid.nunique()
    students_passed = (num_students_passed / df.uid.nunique())
    num_students_no_handins = df.groupby('uid').filter(
        lambda group: all(group.grade == 'Not handed in')).uid.nunique()
    students_no_handins = (num_students_no_handins / df.uid.nunique())

    if args.verbose:
        print("Plotting...")
    fig, (ax1, ax2) = plt.subplots(
        nrows=1, ncols=2,
        sharex=False, sharey=True,
        figsize=(9, 4)
    )
    ax1 = sns.barplot(
        data=plot_data,
        x="percentage",
        y="Assignment",
        hue="grade",
        ax=ax1)
    ax1.axis('tight')

    ax1.axvline(students_passed, linestyle='dashed', color='tab:green',
                label=f'Passed: {100*students_passed:.2f}% - {num_students_passed}/{df.uid.nunique():d}')
    ax1.axvline(students_no_handins, linestyle='dashed', color='tab:red',
                label=f'No handins: {100*students_no_handins:.2f}% - {num_students_no_handins:d}/{df.uid.nunique():d}')

    ax1.set_xlabel(f'Percentage out of {df.uid.nunique():d} students')
    ax1.set_xlim(0, 1.01)
    ax1.legend(title="Submissions", loc=4,
               framealpha=0.3,
               prop={'size': 6})

    if df[(df.grade == "complete") & (df.Assignment == "Week 7-8")].empty:
        df = df.append(dict(
            Assignment="Week 7-8",
            grade="complete",
            attempts=0
        ), ignore_index=True)

    sns.violinplot(
        data=df[df.grade == "complete"],
        y="Assignment",
        x="attempts",
        ax=ax2
    )

    sns.stripplot(
        data=df,
        x="attempts",
        y="Assignment",
        jitter=True,
        zorder=1,
        ax=ax2
    )

    ax2.text(0.98, 0.22,
             tabulate(df2, headers=df2.columns),
             horizontalalignment='right',
             verticalalignment='top',
             transform=ax2.transAxes,
             color='black', fontsize=6,
             bbox=dict(boxstyle="square", alpha=0.15))

    ax2.axis('tight')

    fig.suptitle(datetime.now().strftime("%b %d %Y %T"))
    fig.tight_layout()

    if args.verbose:
        print("Saving figure...")

    if args.show:
        plt.show()
    else:
        fig.savefig(args.out, format='pdf')


if __name__ == '__main__':
    if args.verbose:
        print("setting up connection to absalon...")
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
    assignments = list(course.get_assignments())

    if args.verbose:
        print("Fetching submissions...")
    pbar = Pbar.ProgressBar(redirect_stdout=True)
    scores = list(chain(*[
        [(assignment.name,
          sub.grade,
          sub.attempt,
          sub.user_id,
          course.get_user(sub.user_id).name)
         for sub in list(assignment.get_submissions())]
        for assignment in pbar(assignments)]))

    # Parallel execution does not work
    # scores = list(chain(*[
    #     p_map(
    #         lambda sub: (
    #             assignment.name,
    #             sub.grade,
    #             sub.attempts,
    #             sub.user_id,
    #             course.get_user(sub.user_id).name),
    #         list(assignment.get_submissions()))
    #     for assignment in assignments]))

    # Count unique values i.e. complete, incomplete and not handed in
    df = pd.DataFrame(scores, columns=['Assignment',
                                       'grade', "attempts", "uid", "uname"])
    df.loc[df.Assignment == "Week1-2", "Assignment"] = "Week 1-2"
    df.grade.fillna('Not handed in', inplace=True)  # replace nan with not handed in
    df.attempts.fillna(0, inplace=True)  # replace nan with not handed in
    df = (
        df.apply(pd.to_numeric, errors="coerce")
        .fillna(df)
        .reset_index(drop=True)
    )

    if args.verbose:
        print("Aggregating data for plotting...")
    plot_scores(df, course, args)
    print("Done!")
