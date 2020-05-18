# Import the Canvas class
from canvasapi import Canvas
from glob import glob
import os
import progressbar as Pbar
import urllib.request
from joblib import Parallel, delayed
import multiprocessing
from time import time
import argparse
import shutil

parser = argparse.ArgumentParser("""
Program to download assignments. It needs two files next to it
    course_id: Containing the course id
    token:     Your personal accesstoken from canvas""")
parser.add_argument("-v", "--verbose",
                    help="sets verbosity",
                    action='store_true')
parser.add_argument("-p", "--parallel",
                    help="download in parallel",
                    action='store_true')

args = parser.parse_args()


def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())


def file_to_string(file_name):
    with open(file_name) as f:
        content = f.read()
    return content.strip()


def download_submission(sub):
    global old_files, args
    try:
        url = sub.attachments[0]['url']
        if url:
            # Fomat file-name like absalon
            file_name = []

            # reorder name as last/first/middle
            name = course.get_user(sub.user_id).name.lower().split()
            name = ''.join(name[-1:] + name[:-1])
            file_name.append(name)

            # add if late
            if sub.late:
                file_name.append('LATE')

            # get student id
            file_name.append(sub.user_id)

            # attachment id
            file_name.append(sub.attachments[0]['id'])

            # also filename from absalon
            tmp_fname = '.'.join(
                sub.attachments[0]['display_name'].split('.')[:-1])
            file_name.append(tmp_fname)

            # Combine to finale output name
            file_name = '_'.join([str(i) for i in file_name])

            # check if user has old submissions
            folders_to_remove = [old for old in old_files
                                 if str(sub.user_id) in old
                                 and file_name+'/' not in old]

            for f in folders_to_remove:
                shutil.rmtree(f)

            # download attachment if it doesn't exist,
            if 'yang' in file_name:
                print("######:", directory+file_name+'.zip')
            if directory+file_name+'/' not in old_files:
                url = sub.attachments[0]['url']
                download_url(url, directory+file_name+'.zip')

    except AttributeError:
        if args.verbose:
            print("Submission has no attachment:", sub.id)

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

# get users
users = course.get_users()

# Walk through all assignments
for assignment in course.get_assignments():

    # Create paths for zip files
    print("Downloading " + assignment.name + "...")
    directory = assignment.name.replace(' ', '') + '/' + 'submissions/'
    if not os.path.exists(directory):
        os.makedirs(directory)
        old_files = []
    else:
        old_files = glob(directory+'*/')

    # Let's parallellize this to increase the speed
    pbar = Pbar.ProgressBar(redirect_stdout=True)
    submissions = list(assignment.get_submissions())
    num_cores = multiprocessing.cpu_count()

    if args.parallel:
        Parallel(n_jobs=num_cores)(delayed(
            download_submission)(sub) for sub in pbar(submissions))
    else:
        for sub in pbar(submissions):
            download_submission(sub)

    # shutil.make_archive(directory[:-1], 'zip', directory)
