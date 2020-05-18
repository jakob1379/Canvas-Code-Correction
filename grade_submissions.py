# Import the Canvas class
from canvasapi import Canvas
from glob import glob
import os
import urllib.request
import numpy as np
import re
import progressbar as Pbar

def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())

def file_to_string(file_name):
    with open(file_name) as f:
        content = f.read()
    return content.strip()


# %% Init
print('Initialising canvas...')

# Canvas API URL
domain = 'absalon.ku.dk'
API_URL = "https://"+domain+"/"

# Canvas API key
API_KEY = file_to_string('token')

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

# init course
course_id = file_to_string('course-id')
course = canvas.get_course(course_id)

# get users
users = course.get_users()



assignment = course.get_assignments()[0]
reports = sorted(glob(base_dir + 'Week*/submissions/*/'))

score_to_complete = 43
scores_to_complete = dict(1=43, 2=50, 3=50, 4=50)
# pbar = Pbar.ProgressBar(redirect_stdout=True)
# for rep in pbar(reports):
for rep in reports:
    fname = rep.split('/')[-1]

    # get points and user id
    points = np.loadtxt(glob(rep+'/*point*')[0]).sum()
    file_to_upload = glob(rep+'/*.zip')[0]
    user_id = re.findall(r'\d+', fname)[0]

    # Get submission for user
    submission = assignment.get_submission(user_id)

    # Grade accordingly

    # out_str = 'Checking: ' + fname
    # if submission.grade == 'complete':
    #     print(out_str)
    #     print("Already passed!")
    #     continue
    # elif points >= score_to_complete and submission.grade != 'complete':
    #     print(out_str)
    #     print("Completed with points:", points)
    #     print()
    #     submission.edit(submission={'posted_grade': 'complete'})
    # elif points < score_to_complete and (submission.grade != 'incomplete' and
    #                       submission.grade != 'incomplete'):
    #     print(out_str)
    #     print("Incomplete with points:", points)
    #     print()
    #     submission.edit(submission={'posted_grade': 'incomplete'})


    break
