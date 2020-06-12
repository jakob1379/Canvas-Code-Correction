# Import the Canvas class
from canvasapi import Canvas
from glob import glob
from joblib import Parallel, delayed
from time import time
import argparse
import multiprocessing
import os
import progressbar as Pbar
import re
import shutil
import urllib.request


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def download_url(url, save_path):
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())


def file_to_string(file_name):
    with open(file_name) as f:
        content = f.read()
    return content.strip()


def print_dict(d):
    max_key = len(max(d.keys(), key=len))
    for k, v in d.items():
        print(k.ljust(max_key) + ': ' + str(v))
    print()


def print_as_dict(dd):
    d = vars(dd)
    max_key = len(max(d.keys(), key=len))
    for k, v in d.items():
        print(k.ljust(max_key) + ': ' + str(v))
    print()


def extract_comment_filenames(comments):
    # Get all attachments in comments as one flat list
    return flatten_list(
        [[unquote(att.get('filename')) for att in comm.get('attachments')
          if att.get('filename')]
         for comm in comments if comm.get('attachments')])


def flatten_list(list_of_lists):
    if any([not isinstance(alist, list) for alist in list_of_lists]):
        return list_of_lists
    return [y for x in list_of_lists for y in x]


def create_file_name(submission, course, method='name'):
    file_name = []
    uid = submission.user_id

    # Get users name as sur/first/middle
    if method == 'sortable':
        user_name = re.sub(
            "[, ]", "", course.get_user(uid).sortable_name.lower())
    elif method == 'name':
        user_name = course.get_user(uid).name.lower().split(' ')
        user_name = ''.join(user_name[-1:] + user_name[:-1])
    file_name.append(user_name)

    # add if late
    if submission.late:
        file_name.append('LATE')

    # get student id
    file_name.append(uid)

    # attachment id
    attachment = submission.attachments[0]
    file_name.append(attachment['id'])

    # also filename from absalon
    tmp_fname = '.'.join(
        attachment['display_name'].split('.')[:-1])
    file_name.append(tmp_fname)

    # Combine to finale output user_name
    return '_'.join([str(i) for i in file_name])
