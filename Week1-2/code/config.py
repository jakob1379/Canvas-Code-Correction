'''
Config file
'''
# test files
test_files = ["test_2_6.cpp","test_3_3.cpp","test_5_3.cpp","test_5_4.cpp","test_5_6.cpp","test_5_9.cpp","test_5_10.cpp"]
TIME_LIMIT = 30 #seconds per exercise

head_lines = {}
head_lines["test_2_6.cpp"] = "Exercise 2.6"
head_lines["test_3_3.cpp"] = "Exercise 3.3"
head_lines["test_5_3.cpp"] = "Exercise 5.3"
head_lines["test_5_4.cpp"] = "Exercise 5.4"
head_lines["test_5_6.cpp"] = "Exercise 5.6"
head_lines["test_5_9.cpp"] = "Exercise 5.9"
head_lines["test_5_10.cpp"] = "Exercise 5.10"

# point for each function
minus_point_for_memory_leak = 0.2
total_points = {}
total_points["test_2_6.cpp"] = 7
total_points["test_3_3.cpp"] = 7
total_points["test_5_3.cpp"] = 7
total_points["test_5_4.cpp"] = 7
total_points["test_5_6.cpp"] = 7
total_points["test_5_9.cpp"] = 7
total_points["test_5_10.cpp"] = 8

# number of subtests
numberOfSubtests = {}
numberOfSubtests["test_2_6.cpp"] = 1
numberOfSubtests["test_3_3.cpp"] = 2
numberOfSubtests["test_5_3.cpp"] = 2
numberOfSubtests["test_5_4.cpp"] = 4
numberOfSubtests["test_5_6.cpp"] = 5
numberOfSubtests["test_5_9.cpp"] = 2
numberOfSubtests["test_5_10.cpp"] = 3


#object files
object_files = {}
object_files["test_2_6.cpp"] = "e26"
object_files["test_3_3.cpp"] = "e33"
object_files["test_5_3.cpp"] = "e53"
object_files["test_5_4.cpp"] = "e54"
object_files["test_5_6.cpp"] = "e56"
object_files["test_5_9.cpp"] = "e59"
object_files["test_5_10.cpp"] = "e510"


# files that are not part of the submissions, but are needed for each test file (in the order the should
# compiled in)
other_files = {}
other_files["test_2_6.cpp"] = "test/BasicTest.cpp"
other_files["test_3_3.cpp"] = "test/BasicTest.cpp test/TA_3_3.cpp"
other_files["test_5_3.cpp"] = "test/BasicTest.cpp"
other_files["test_5_4.cpp"] = "test/BasicTest.cpp"
other_files["test_5_6.cpp"] = "test/BasicTest.cpp"
other_files["test_5_9.cpp"] = "test/BasicTest.cpp"
other_files["test_5_10.cpp"] = "test/BasicTest.cpp"

# submission files associated with the test files
sub_files = {}
sub_files["test_2_6.cpp"] = "2_6.cpp"
sub_files["test_3_3.cpp"] = "3_3.cpp"
sub_files["test_5_3.cpp"] = "5_3.cpp"
sub_files["test_5_4.cpp"] = "5_4.cpp"
sub_files["test_5_6.cpp"] = "5_6.cpp"
sub_files["test_5_9.cpp"] = "5_9.cpp"
sub_files["test_5_10.cpp"] = "5_10.cpp"

compiler_lines = []
for test in test_files:
	compiler_lines.append( "clang++ -std=c++11 -w -o " + object_files[test] + " " + sub_files[test] + " " + 
		other_files[test] + " " + "test/" + test + " ")
