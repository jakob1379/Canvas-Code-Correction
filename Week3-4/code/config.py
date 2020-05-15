'''
Config file
'''
# test files
TIME_LIMIT = 30 #seconds per exercise
test_files = ["test_6_1_1.cpp","test_6_1_2.cpp","test_6_1_3.cpp","test_6_1_4.cpp","test_6_1_5.cpp","test_6_1_6.cpp","test_6_1_7.cpp", \
			  "test_6_2_1.cpp","test_6_2_2.cpp","test_6_2_3.cpp","test_6_2_4.cpp","test_6_2_5.cpp","test_6_2_6.cpp","test_6_2_7.cpp","test_6_2_8.cpp","test_6_2_9.cpp", \
			  "test_7_1_1.cpp","test_7_1_2.cpp","test_7_1_3.cpp","test_7_1_4.cpp","test_7_1_5.cpp", \
			  "test_8_2.cpp", \
			  "test_9_1.cpp"]
'''
["test_6_1_1.cpp"]
["test_6_1_2.cpp"]
["test_6_1_3.cpp"]
["test_6_1_4.cpp"]
["test_6_1_5.cpp"]
["test_6_1_6.cpp"]
["test_6_1_7.cpp"]

["test_6_2_1.cpp"]
["test_6_2_2.cpp"]
["test_6_2_3.cpp"]
["test_6_2_4.cpp"]
["test_6_2_5.cpp"]
["test_6_2_6.cpp"]
["test_6_2_7.cpp"]
["test_6_2_8.cpp"]
["test_6_2_9.cpp"]

["test_7_1_1.cpp"]
["test_7_1_2.cpp"]
["test_7_1_3.cpp"]
["test_7_1_4.cpp"]
["test_7_1_5.cpp"]

["test_7_3_2.cpp"]
["test_7_3_4.cpp"]

["test_8_2.cpp"] 
["test_9_1.cpp"]
'''

head_lines = {}
head_lines["test_6_1_1.cpp"] = "Exercise 6.1.1"
head_lines["test_6_1_2.cpp"] = "Exercise 6.1.2"
head_lines["test_6_1_3.cpp"] = "Exercise 6.1.3"
head_lines["test_6_1_4.cpp"] = "Exercise 6.1.4"
head_lines["test_6_1_5.cpp"] = "Exercise 6.1.5"
head_lines["test_6_1_6.cpp"] = "Exercise 6.1.6"
head_lines["test_6_1_7.cpp"] = "Exercise 6.1.7"

head_lines["test_6_2_1.cpp"] = "Exercise 6.2.1"
head_lines["test_6_2_2.cpp"] = "Exercise 6.2.2"
head_lines["test_6_2_3.cpp"] = "Exercise 6.2.3"
head_lines["test_6_2_4.cpp"] = "Exercise 6.2.4"
head_lines["test_6_2_5.cpp"] = "Exercise 6.2.5"
head_lines["test_6_2_6.cpp"] = "Exercise 6.2.6"
head_lines["test_6_2_7.cpp"] = "Exercise 6.2.7"
head_lines["test_6_2_8.cpp"] = "Exercise 6.2.8"
head_lines["test_6_2_9.cpp"] = "Exercise 6.2.9"

head_lines["test_7_1_1.cpp"] = "Exercise 7.1.1"
head_lines["test_7_1_2.cpp"] = "Exercise 7.1.2"
head_lines["test_7_1_3.cpp"] = "Exercise 7.1.3"
head_lines["test_7_1_4.cpp"] = "Exercise 7.1.4"
head_lines["test_7_1_5.cpp"] = "Exercise 7.1.5"

#head_lines["test_7_3_2.cpp"] = "Exercise 7.3.2"
#head_lines["test_7_3_4.cpp"] = "Exercise 7.3.4"

head_lines["test_8_2.cpp"] = "Exercise 8.2"
head_lines["test_9_1.cpp"] = "Exercise 9.1"

# point for each function
minus_point_for_memory_leak = 0.2
total_points = {}
total_points["test_6_1_1.cpp"] = 10.0/7
total_points["test_6_1_2.cpp"] = 10.0/7
total_points["test_6_1_3.cpp"] = 10.0/7
total_points["test_6_1_4.cpp"] = 10.0/7
total_points["test_6_1_5.cpp"] = 10.0/7
total_points["test_6_1_6.cpp"] = 10.0/7
total_points["test_6_1_7.cpp"] = 10.0/7

total_points["test_6_2_1.cpp"] = 12.0/9
total_points["test_6_2_2.cpp"] = 12.0/9
total_points["test_6_2_3.cpp"] = 12.0/9
total_points["test_6_2_4.cpp"] = 12.0/9
total_points["test_6_2_5.cpp"] = 12.0/9
total_points["test_6_2_6.cpp"] = 12.0/9
total_points["test_6_2_7.cpp"] = 12.0/9
total_points["test_6_2_8.cpp"] = 12.0/9
total_points["test_6_2_9.cpp"] = 12.0/9

total_points["test_7_1_1.cpp"] = 10.0/5
total_points["test_7_1_2.cpp"] = 10.0/5
total_points["test_7_1_3.cpp"] = 10.0/5
total_points["test_7_1_4.cpp"] = 10.0/5
total_points["test_7_1_5.cpp"] = 10.0/5

#total_points["test_7_3_2.cpp"] = 10.0
#total_points["test_7_3_4.cpp"] = 3.0

total_points["test_8_2.cpp"] = 13
total_points["test_9_1.cpp"] = 5

# number of subtests
numberOfSubtests = {}
numberOfSubtests["test_6_1_1.cpp"] = 2 
numberOfSubtests["test_6_1_2.cpp"] = 2
numberOfSubtests["test_6_1_3.cpp"] = 1
numberOfSubtests["test_6_1_4.cpp"] = 1
numberOfSubtests["test_6_1_5.cpp"] = 1
numberOfSubtests["test_6_1_6.cpp"] = 1
numberOfSubtests["test_6_1_7.cpp"] = 1

numberOfSubtests["test_6_2_1.cpp"] = 1
numberOfSubtests["test_6_2_2.cpp"] = 1
numberOfSubtests["test_6_2_3.cpp"] = 1
numberOfSubtests["test_6_2_4.cpp"] = 1
numberOfSubtests["test_6_2_5.cpp"] = 1
numberOfSubtests["test_6_2_6.cpp"] = 1
numberOfSubtests["test_6_2_7.cpp"] = 1
numberOfSubtests["test_6_2_8.cpp"] = 2
numberOfSubtests["test_6_2_9.cpp"] = 1

numberOfSubtests["test_7_1_1.cpp"] = 1
numberOfSubtests["test_7_1_2.cpp"] = 1
numberOfSubtests["test_7_1_3.cpp"] = 1
numberOfSubtests["test_7_1_4.cpp"] = 1
numberOfSubtests["test_7_1_5.cpp"] = 1

#numberOfSubtests["test_7_3_2.cpp"] = 1
#numberOfSubtests["test_7_3_4.cpp"] = 1

numberOfSubtests["test_8_2.cpp"] = 2 
numberOfSubtests["test_9_1.cpp"] = 2


#object files
object_files = {}
object_files["test_6_1_1.cpp"] = "e611"
object_files["test_6_1_2.cpp"] = "e612"
object_files["test_6_1_3.cpp"] = "e613"
object_files["test_6_1_4.cpp"] = "e614"
object_files["test_6_1_5.cpp"] = "e615"
object_files["test_6_1_6.cpp"] = "e616"
object_files["test_6_1_7.cpp"] = "e617"

object_files["test_6_2_1.cpp"] = "e621"
object_files["test_6_2_2.cpp"] = "e622"
object_files["test_6_2_3.cpp"] = "e623"
object_files["test_6_2_4.cpp"] = "e624"
object_files["test_6_2_5.cpp"] = "e625"
object_files["test_6_2_6.cpp"] = "e626"
object_files["test_6_2_7.cpp"] = "e627"
object_files["test_6_2_8.cpp"] = "e628"
object_files["test_6_2_9.cpp"] = "e629"

object_files["test_7_1_1.cpp"] = "e711"
object_files["test_7_1_2.cpp"] = "e712"
object_files["test_7_1_3.cpp"] = "e713"
object_files["test_7_1_4.cpp"] = "e714"
object_files["test_7_1_5.cpp"] = "e715"

#object_files["test_7_3_2.cpp"] = "e732"
#object_files["test_7_3_4.cpp"] = "e734"

object_files["test_8_2.cpp"] = "e82"
object_files["test_9_1.cpp"] = "e91"


# files that are not part of the submissions, but are needed for each test file (in the order they should be
# compiled in)
other_files = {}
other_files["test_6_1_1.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_2.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_3.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_4.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_5.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_6.cpp"] = "test/BasicTest.cpp"
other_files["test_6_1_7.cpp"] = "test/BasicTest.cpp"

other_files["test_6_2_1.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_2.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_3.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_4.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_5.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_6.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_7.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_8.cpp"] = "test/BasicTest.cpp"
other_files["test_6_2_9.cpp"] = "test/BasicTest.cpp"

other_files["test_7_1_1.cpp"] = "test/BasicTest.cpp"
other_files["test_7_1_2.cpp"] = "test/BasicTest.cpp"
other_files["test_7_1_3.cpp"] = "test/BasicTest.cpp"
other_files["test_7_1_4.cpp"] = "test/BasicTest.cpp"
other_files["test_7_1_5.cpp"] = "test/BasicTest.cpp"

#other_files["test_7_3_2.cpp"] = "test/BasicTest.cpp"
#other_files["test_7_3_4.cpp"] = "test/BasicTest.cpp"

other_files["test_8_2.cpp"] = "test/BasicTest.cpp"
other_files["test_9_1.cpp"] = "test/BasicTest.cpp"

# submission files associated with the test files
sub_files = {}
sub_files["test_6_1_1.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_2.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_3.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_4.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_5.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_6.cpp"] = "ComplexNumber.cpp"
sub_files["test_6_1_7.cpp"] = "ComplexNumber.cpp CalculateExponential.cpp"

sub_files["test_6_2_1.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_2.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_3.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_4.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_5.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_6.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_7.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_8.cpp"] = "Matrix2x2.cpp"
sub_files["test_6_2_9.cpp"] = "Matrix2x2.cpp"

sub_files["test_7_1_1.cpp"] = "Student.cpp"
sub_files["test_7_1_2.cpp"] = "Student.cpp" 
sub_files["test_7_1_3.cpp"] = "Student.cpp GraduateStudent.cpp"
sub_files["test_7_1_4.cpp"] = "Student.cpp GraduateStudent.cpp"
sub_files["test_7_1_5.cpp"] = "Student.cpp GraduateStudent.cpp PhdStudent.cpp"

#sub_files["test_7_3_2.cpp"] = "AbstractOdeSolver.cpp FowardEulerSolver.cpp"
#sub_files["test_7_3_4.cpp"] = "AbstractOdeSolver.cpp RungeKuttaSolver.cpp"

sub_files["test_8_2.cpp"] = "" 
sub_files["test_9_1.cpp"] = "Exception.cpp OutOfRangeException.cpp FileNotOpenException.cpp"

compiler_lines = []
for test in test_files:
	compiler_lines.append( "clang++ -std=c++11 -o " + object_files[test] + " " + sub_files[test] + " " + 
		other_files[test] + " " + "test/" + test + " ")
