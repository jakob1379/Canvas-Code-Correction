'''
Config file
'''
# test files
TIME_LIMIT = 60  # seconds per exercise
test_files = ["LogisticRegression.cpp", "NearestNeighbours.cpp"]

head_lines = {}
head_lines["LogisticRegression.cpp"] = "LogisticRegression compared against reference solution"
head_lines["NearestNeighbours.cpp"] = "NearestNeighbours compared against reference solution"


# point for each function
minus_point_for_memory_leak = 0.2
total_points = {}
total_points["LogisticRegression.cpp"] = 50.0/2
total_points["NearestNeighbours.cpp"] = 50.0/2


# number of subtests
numberOfSubtests = {}
numberOfSubtests["LogisticRegression.cpp"] = 0
numberOfSubtests["NearestNeighbours.cpp"] = 0


# object files
object_files = {}
object_files["LogisticRegression.cpp"] = "lr"
object_files["NearestNeighbours.cpp"] = "nn"


# files that are not part of the submissions, but are needed for each test file (in the order they should be
# compiled in)
other_files = {}
other_files["LogisticRegression.cpp"] = "LogisticRegression.cpp"
other_files["NearestNeighbours.cpp"] = "NearestNeighbours.cpp"


# submission files associated with the test files
sub_files = {}
sub_files["LogisticRegression.cpp"] = ""
sub_files["NearestNeighbours.cpp"] = ""


compiler_lines = []
for test in test_files:
    compiler_lines.append("clang++ -std=c++11 -o " +
                          object_files[test] + " " + other_files[test])
