import argparse
import configparser
import multiprocessing
from datetime import datetime
from functools import partial
from itertools import chain

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import progressbar as Pbar
import seaborn as sns
from canvasapi import Canvas
from matplotlib.lines import Line2D
from p_tqdm import p_map
from tabulate import tabulate
from pathlib import Path
from canvas_helpers import init_canvas_course

plt.style.use('ggplot')
config = configparser.ConfigParser()
config.read('config.ini')

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
parser.add_argument("-i", "--interactive",
                    help="Open the dataframe in an interactive window",
                    action='store_true')

parser.add_argument("-v", "--verbose",
                    help="set verbose",
                    action='store_true')
parser.add_argument("--save-data",
                    help="Save user data to a temporary file",
                    action='store_true')
parser.add_argument("--load-data",
                    help="Load previous data if any available",
                    action='store_true')

args = parser.parse_args()


def load_data(course):
    """ Fetch data for all assignment and convert to pandas df

    :param course: canvas course object
    :returns: DataFrame
    :rtype: pd.DataFrame

    """

    if args.load_data and Path("tmp").joinpath("data.csv").exists():
        df = pd.read_csv(Path("tmp").joinpath("data.csv"))
        return df

    assignments = list(course.get_assignments())

    if args.verbose:
        print("Fetching submissions from each assignment...")

    scores = []
    pbar = Pbar.ProgressBar(redirect_stdout=True,
                            max_value=Pbar.UnknownLength)
    counter = 0
    for assignment in assignments:
        for sub in assignment.get_submissions():
            pbar.update(counter)
            scores.append(
                (assignment.name,
                 sub.attempt,
                 sub.entered_grade,
                 sub.entered_score,
                 sub.grade,
                 sub.score,
                 sub.user_id,
                 course.get_user(sub.user_id).name)
            )
            counter += 1
    pbar.finish()

    # Count unique values i.e. complete, incomplete and not handed in
    df = pd.DataFrame(scores,
                      columns=['Assignment',
                               'attempts',
                               'entered_grade',
                               'entered_score',
                               'grade',
                               'score',
                               'user_id',
                               "uname"])

    # replace nan with not handed in
    df.entered_grade.fillna('Not handed in', inplace=True)

    df.attempts.fillna(0, inplace=True)
    df = (
        df.apply(pd.to_numeric, errors="coerce")
        .fillna(df)
        .reset_index(drop=True)
    )
    df['passed'] = (
        df.groupby("Assignment")
        .apply(lambda group:
               config.getfloat("scores_to_complete", group.name) *
               group.entered_score >=
               config.getfloat("scores_to_complete", group.name))
        .reset_index(drop=True))
    df.loc[df['passed'] == True, 'passed'] = 'Passed'
    df.loc[df['passed'] == False, 'passed'] = 'Not passed'
    df.loc[df['entered_grade'] == "Not handed in", 'passed'] = 'Not handed in'
    df['entered_score'] = df.entered_score.astype(np.float64)
    df['score'] = df.score.astype(np.float64)

    if args.save_data:
        df.to_csv(Path("tmp").joinpath("data.csv"), index=False)
    return df


def plot_scores(df_in):
    """ Creates a statistical overview of the submissions for the course

    :param df_in: Dataframe to use
    :param arguments:
    :returns:
    :rtype:

    """

    df = df_in.copy()

    # calc how many
    plot_data = (
        df
        .groupby(["Assignment", "passed"])
        .apply(lambda group: len(group)/df.user_id.nunique())
        .to_frame("percentage")
        .reset_index()
        .sort_values(by="Assignment"))

    df2 = (
        df[df["passed"] == "Passed"]
        .groupby("Assignment")
        .agg({"attempts": ["median", "mad", "mean", "var", "max"]})
        .reset_index()
        .set_index("Assignment")
        .round(2)
    )
    df2.index.name = None
    # Remove unnecessary multindex
    df2.columns = df2.columns.droplevel(0)

    if args.verbose:
        print("Counting students who have passed assignments...")
        # Count how many have passed the course
    nunique_students = df.user_id.nunique()
    num_students_passed = df.groupby('user_id').filter(
        lambda group: len(set(group.entered_grade)) == 1).user_id.nunique()
    students_passed = (num_students_passed / nunique_students)
    num_students_no_handins = df.groupby('user_id').filter(
        lambda group: all(group.entered_grade == 'Not handed in')).user_id.nunique()
    students_no_handins = (num_students_no_handins / nunique_students)
    students_attempted_and_passed = (
        num_students_passed / (nunique_students - num_students_no_handins))

    if args.verbose:
        print("Plotting...")
    fig, (ax1, ax2) = plt.subplots(
        nrows=1, ncols=2,
        sharex=False, sharey=True,
        figsize=(12, 9)
    )

    ax1 = sns.barplot(
        data=plot_data,
        x="percentage",
        y="Assignment",
        hue="passed",
        ax=ax1)
    ax1.axis('tight')

    ax1.axvline(
        students_passed,
        linestyle='dashed',
        color='tab:green',
        label=f'Passed: {100*students_passed:.2f}% - {num_students_passed}/{nunique_students:d}')

    # Add a legend showing percentage of students who attempted AND passed
    attempt_passed_line = Line2D(
        [0], [0],
        label=f'Attempted and passed: {100*students_attempted_and_passed:.2f}% - {num_students_passed}/{nunique_students - num_students_no_handins:d}', color='tab:blue',
        linestyle="dashed")

    ax1.axvline(
        students_no_handins,
        linestyle='dashed',
        color='tab:red',
        label=f'No handins: {100*students_no_handins:.2f}% - {num_students_no_handins:d}/{nunique_students:d}')

    line_handles, _ = ax1.get_legend_handles_labels()
    line_handles.append(attempt_passed_line)

    ax1.set_xlabel(f'Percentage out of {nunique_students:d} students')
    ax1.set_xlim(0, 1.01)
    bar_handles = ax1.get_legend_handles_labels()[3:]

    ax1.legend(handles=list(line_handles) + list(bar_handles),
               title="Submissions", loc=4,
               framealpha=0.3,
               prop={'size': 8})

    sns.violinplot(
        data=df[df['passed'] == 'Passed'],
        y="Assignment",
        x="attempts",
        color=".75",
        linewidth=0,
        ax=ax2
    )

    sns.stripplot(
        data=df,
        x="attempts",
        y="Assignment",
        jitter=True,
        zorder=1,
        alpha=0.4,
        linewidth=1,
        edgecolor='black',
        ax=ax2
    )

    ax2.text(1, 0,
             tabulate(df2, headers=df2.columns),
             horizontalalignment='right',
             verticalalignment='bottom',
             transform=ax2.transAxes,
             color='black', fontsize=8,
             bbox=dict(boxstyle="square", alpha=0.10),
             fontfamily='monospace')

    ax2.set_xlabel("Attemps used for passed assignments")
    ax2.axis('tight')

    fig.suptitle(datetime.now().strftime("%b %d %Y %T"))
    fig.tight_layout()

    if args.verbose:
        print("Saving figure...")

    if args.show:
        plt.show()
    else:
        fig.savefig(args.out, format='pdf')


def main():
    if args.verbose:
        print("setting up connection to absalon...")

    # Initialize a new Canvas course object
    course = init_canvas_course(config)

    df = load_data(course)

    if args.verbose:
        print("Aggregating data for plotting...")
    plot_scores(df)
    print("Done!")

    if args.interactive:
        import dtale
        dtale.show(df, open_browser=True)


if __name__ == '__main__':
    main()
