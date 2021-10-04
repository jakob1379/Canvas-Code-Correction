# Import the Canvas class
from canvasapi import Canvas
import re
from pathlib import Path
import os
import urllib.request
from hashlib import md5
import bcolors

# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'


def download_url(url, save_path):
    """ files files at url to the given path
    :param url: target url
    :param save_path: target path
    """

    # Make sure destination folder exists
    end_folder = os.sep.join(save_path.split(os.sep)[:-1])
    if end_folder:
        (
            Path(end_folder)
            .mkdir(parents=True, exist_ok=True)
        )
    with urllib.request.urlopen(url) as dl_file:
        with open(save_path, 'wb') as out_file:
            out_file.write(dl_file.read())


def file_to_string(file_name):
    """ reads entire file into a single string

    :param file_name: path
    :returns: file content as string
    :rtype: str

    """

    with open(file_name, "r") as f:
        content = f.read()
    return content.strip()


def print_dict(d):
    """ pretty prints a dictionary

    :param d: dictionary to print

    """

    max_key = len(max(d.keys(), key=len))
    for k, v in d.items():
        print(k.ljust(max_key) + ' : ' + str(v))
    print()


def print_as_dict(dd):
    """ Function that takes an input and tries to pretty print its variables and methods. __dict__ must be defined

    :param dd: any input that has a __dict__ defined

    """

    d = vars(dd)
    keys = sorted(d.keys())
    values = [d[keys] for key in keys]
    max_key = len(max(d.keys(), key=len))
    for k, v in zip(keys, values):
        print(k.ljust(max_key) + ' : ' + str(v))
    print()


def md5sum(fname):
    """ Calculates the md5sum of a given file

    :param fname: path to file
    :returns: md5sum
    :rtype: str

    """

    m = md5()
    with open(fname, "rb") as f:
        # read file in chunk and call update on each chunk if file is large.
        data = f.read()
        m.update(data)
    return m.hexdigest()


def extract_comment_filenames(comments):
    """ extract all filenames from submission comments

    :param comments:
    :returns: list of filenames
    :rtype: list

    """

    # Get all attachments in comments as one flat list
    fileNames = []
    for comment in list(comments):
        if comment.get("attachments"):
            for attachment in list(comment.get("attachments")):
                if attachment.get("filename"):
                    fileNames.append(attachment.get("filename"))
    return fileNames


def create_file_name(submission, course, method='name'):
    """ constructs the basename for a submission

    :param submission: canvas submission object
    :param course: canvas course object
    :param method: what name type to use
    :returns: basename to use with files
    :rtype: str

    """

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


def init_canvas_course(config):
    canvas = Canvas(config['DEFAULT']['apiurl'], config['DEFAULT']['token'])

    # init course
    course_id = config['DEFAULT']['courseid']
    course = canvas.get_course(course_id)
    return course
