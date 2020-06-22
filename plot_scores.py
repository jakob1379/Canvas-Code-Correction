# Import the Canvas class
from canvas_helpers import (file_to_string,
                            flatten_list)
from canvasapi import Canvas
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import progressbar as Pbar
plt.style.use('ggplot')

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
        [[(assignment.name, sub.grade) for sub in assignment.get_submissions()]
                                    for assignment in assignments]))

# Count unique values i.e. complete, incomplete and not handed in
df = pd.DataFrame(scores, columns=['Assignment', 'grade'])
df.fillna('Not handed in', inplace=True) #replace nan with not handed in
plot_data = df.groupby('Assignment')['grade'].value_counts(
    dropna=False, normalize=True).unstack()

# Count how many have passed the course
# get students
print("counting students who passed")
students = [student.id for student in course.get_users(enrollment_type=['student'])]
pbar = Pbar.ProgressBar()
students_passed = sum(
    [all([
        ass.get_submission(stud_id).grade for ass in assignments])
     for stud_id in pbar(students)]
)


# normalize
students_passed /= len(students)
# plot_data['passed'] = np.nan
# plot_data = plot_data.append(pd.Series(name='Passed'))
# plot_data.passed['Passed'] = students_passed

fig, ax = plt.subplots(nrows=1, ncols=1,
                       sharex=False, sharey=False,
                       figsize=(9, 4))
ax = plot_data.plot.barh(ax=ax,
                         edgecolor='k')
ax.axvline(students_passed, linestyle='dashed', color='tab:green',
           label='Students Passed')

ax.set_xlabel('Grade count')
ax.set_xlim(0, 1)
plt.legend(loc='best')
plt.tight_layout()
plt.savefig('scores.pdf', format='pdf')
plt.show()

print("Done!")
