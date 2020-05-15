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

parser = argparse.ArgumentParser("""
Program to download assignments. It needs two files next to it
    course_id: Containing the course id
    token:     Your personal accesstoken from canvas""")
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
            file_name.append(sub.attachments[0]['display_name'])
            file_name = [str(i) for i in file_name]

            # Join name to simple file name
            file_name = '_'.join(file_name)

            # check if user has old submissions
            for old_file in old_files:
                if str(sub.user_id) in old_file and file_name not in old_file:
                    os.remove(old_file)

            # Delete old folder from correction directory
            old_corrections = glob('localCodeChecker_Rune/submissions/*')
            for old_file in old_corrections:
                if str(sub.user_id) in old_file and \
                   sub.attachment[0]['id'] not in old_file:
                    os.rmdir(old_file)

            # download attachment if it doesn't exist,
            if directory+file_name not in old_files:
                url = sub.attachments[0]['url']
                download_url(url, directory+file_name)

    except AttributeError:
        pass


# parser = argparse.ArgumentParser()
# parser.add_argument("-c", "--course-id",
#                     help="path to file containing id of the course",
#                     metavar="course",
#                     type=str,
#                     nargs='?',
#                     default='.saved_course_id')
# parser.add_argument("-t", "--token",
#                     help="path to absalon token.",
#                     metavar="token",
#                     type=str,
#                     default='.saved_token')
# parser.add_argument("arg", help="required positional arg")
# args = parser.parse_args()

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
    print(f"Checking {assignment.name}...")
    directory = assignment.name.replace(' ', '') + '/' + 'submissions/'
    if not os.path.exists(directory):
        os.makedirs(directory)
        old_files = []
    else:
        old_files = glob(directory+'*')

    # Let's parallellize this to increase the speed
    pbar = Pbar.ProgressBar(redirect_stdout=True)
    submissions = list(assignment.get_submissions())
    num_cores = multiprocessing.cpu_count()
    Parallel(n_jobs=num_cores)(
        delayed(
            download_submission)(i) for i in pbar(submissions))
    # shutil.make_archive(directory[:-1], 'zip', directory)
