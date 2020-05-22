'''
Config file
'''
# test files
TIME_LIMIT = 60 #seconds per exercise
test_files = ["test_v_1.cpp", "test_v_2.cpp", "test_v_3.cpp" , "test_v_6.cpp", \
              "test_v_8.cpp", "test_v_9.cpp", "test_v_10.cpp", "test_v_11.cpp", "test_v_12.cpp", \
              "test_m_1.cpp", "test_m_2.cpp", "test_m_3.cpp", "test_m_4.cpp", "test_m_6.cpp", \
              "test_m_7.cpp", "test_m_8.cpp", "test_m_9.cpp", "test_m_10.cpp", "test_m_11.cpp","test_m_12.cpp", \
              "test_s_1.cpp", "test_s_2.cpp", "test_s_3.cpp", "test_s_4.cpp", "test_s_5.cpp"  ]

head_lines = {}
head_lines["test_v_1.cpp"] = "Vector exercise: constructor"
head_lines["test_v_2.cpp"] = "Vector exercise: copy constructor"
head_lines["test_v_3.cpp"] = "Vector exercise: [] operator"
head_lines["test_v_6.cpp"] = "Vector exercise: = operator"
head_lines["test_v_8.cpp"] = "Vector exercise: unary - operator"
head_lines["test_v_9.cpp"] = "Vector exercise: + operator"
head_lines["test_v_10.cpp"] = "Vector exercise: - operator"
head_lines["test_v_11.cpp"] = "Vector exercise: * operator"
head_lines["test_v_12.cpp"] = "Vector exercise: 3 norm"

head_lines["test_m_1.cpp"] = "Matrix exercise: constructor"
head_lines["test_m_2.cpp"] = "Matrix exercise: copy constructor"
head_lines["test_m_3.cpp"] = "Matrix exercise: () operator"
head_lines["test_m_4.cpp"] = "Matrix exercise: = operator"
head_lines["test_m_6.cpp"] = "Matrix exercise: unary - operator"
head_lines["test_m_7.cpp"] = "Matrix exercise: + operator"
head_lines["test_m_8.cpp"] = "Matrix exercise: - operator"
head_lines["test_m_9.cpp"] = "Matrix exercise: * operator"
head_lines["test_m_10.cpp"] = "Matrix exercise: matrix * vector"
head_lines["test_m_11.cpp"] = "Matrix exercise: vector * matrix"
head_lines["test_m_12.cpp"] = "Matrix exercise: internal struct"


head_lines["test_s_1.cpp"] = "Sparse vector exercise: construct"
head_lines["test_s_2.cpp"] = "Sparse vector exercise: insertion, setValue, getValue etc"
head_lines["test_s_3.cpp"] = "Sparse vector exercise: copy ctor"
head_lines["test_s_4.cpp"] = "Sparse vector exercise: assignment operator"
head_lines["test_s_5.cpp"] = "Sparse vector exercise: math operators"

# point for each function
minus_point_for_memory_leak = 0.2
total_points = {}
total_points["test_v_1.cpp"] = 25.0/9
total_points["test_v_2.cpp"] = 25.0/9
total_points["test_v_3.cpp"] = 25.0/9
total_points["test_v_6.cpp"] = 25.0/9
total_points["test_v_8.cpp"] = 25.0/9
total_points["test_v_9.cpp"] = 25.0/9
total_points["test_v_10.cpp"] = 25.0/9
total_points["test_v_11.cpp"] = 25.0/9
total_points["test_v_12.cpp"] = 25.0/9

total_points["test_m_1.cpp"] = 25.0/11
total_points["test_m_2.cpp"] = 25.0/11
total_points["test_m_3.cpp"] = 25.0/11
total_points["test_m_4.cpp"] = 25.0/11
total_points["test_m_6.cpp"] = 25.0/11
total_points["test_m_7.cpp"] = 25.0/11
total_points["test_m_8.cpp"] = 25.0/11
total_points["test_m_9.cpp"] = 25.0/11
total_points["test_m_10.cpp"] = 25.0/11
total_points["test_m_11.cpp"] = 25.0/11
total_points["test_m_12.cpp"] = 25.0/11

total_points["test_s_1.cpp"] = 25 / 5
total_points["test_s_2.cpp"] = 25 / 5
total_points["test_s_3.cpp"] = 25 / 5
total_points["test_s_4.cpp"] = 25 / 5
total_points["test_s_5.cpp"] = 25 / 5

# number of subtests
numberOfSubtests = {}
numberOfSubtests["test_v_1.cpp"] = 2
numberOfSubtests["test_v_2.cpp"] = 2
numberOfSubtests["test_v_3.cpp"] = 2
numberOfSubtests["test_v_6.cpp"] = 2
numberOfSubtests["test_v_8.cpp"] = 2
numberOfSubtests["test_v_9.cpp"] = 2
numberOfSubtests["test_v_10.cpp"] = 2
numberOfSubtests["test_v_11.cpp"] = 2
numberOfSubtests["test_v_12.cpp"] = 1

numberOfSubtests["test_m_1.cpp"] = 2
numberOfSubtests["test_m_2.cpp"] = 2
numberOfSubtests["test_m_3.cpp"] = 2
numberOfSubtests["test_m_4.cpp"] = 2
numberOfSubtests["test_m_6.cpp"] = 2
numberOfSubtests["test_m_7.cpp"] = 2
numberOfSubtests["test_m_8.cpp"] = 2
numberOfSubtests["test_m_9.cpp"] = 2
numberOfSubtests["test_m_10.cpp"] = 2
numberOfSubtests["test_m_11.cpp"] = 2
numberOfSubtests["test_m_12.cpp"] = 1


numberOfSubtests["test_s_1.cpp"] = 1
numberOfSubtests["test_s_2.cpp"] = 1
numberOfSubtests["test_s_3.cpp"] = 1
numberOfSubtests["test_s_4.cpp"] = 1
numberOfSubtests["test_s_5.cpp"] = 1

#object files
object_files = {}
object_files["test_v_1.cpp"] = "tv1"
object_files["test_v_2.cpp"] = "tv2"
object_files["test_v_3.cpp"] = "tv3"
object_files["test_v_6.cpp"] = "tv6"
object_files["test_v_8.cpp"] = "tv8"
object_files["test_v_9.cpp"] = "tv9"
object_files["test_v_10.cpp"] = "tv10"
object_files["test_v_11.cpp"] = "tv11"
object_files["test_v_12.cpp"] = "tv12"

object_files["test_m_1.cpp"] = "tm1"
object_files["test_m_2.cpp"] = "tm2"
object_files["test_m_3.cpp"] = "tm3"
object_files["test_m_4.cpp"] = "tm4"
object_files["test_m_6.cpp"] = "tm6"
object_files["test_m_7.cpp"] = "tm7"
object_files["test_m_8.cpp"] = "tm8"
object_files["test_m_9.cpp"] = "tm9"
object_files["test_m_10.cpp"] = "tm10"
object_files["test_m_11.cpp"] = "tm11"
object_files["test_m_12.cpp"] = "tm12"

object_files["test_s_1.cpp"] = "s1"
object_files["test_s_2.cpp"] = "s2"
object_files["test_s_3.cpp"] = "s3"
object_files["test_s_4.cpp"] = "s4"
object_files["test_s_5.cpp"] = "s5"
# files that are not part of the submissions, but are needed for each test file (in the order they should be
# compiled in)
other_files = {}
other_files["test_v_1.cpp"] = "test/BasicTest.cpp"
other_files["test_v_2.cpp"] = "test/BasicTest.cpp"
other_files["test_v_3.cpp"] = "test/BasicTest.cpp"
other_files["test_v_6.cpp"] = "test/BasicTest.cpp"
other_files["test_v_8.cpp"] = "test/BasicTest.cpp"
other_files["test_v_9.cpp"] = "test/BasicTest.cpp"
other_files["test_v_10.cpp"] = "test/BasicTest.cpp"
other_files["test_v_11.cpp"] = "test/BasicTest.cpp"
other_files["test_v_12.cpp"] = "test/BasicTest.cpp"

other_files["test_m_1.cpp"] = "test/BasicTest.cpp"
other_files["test_m_2.cpp"] = "test/BasicTest.cpp"
other_files["test_m_3.cpp"] = "test/BasicTest.cpp"
other_files["test_m_4.cpp"] = "test/BasicTest.cpp"
other_files["test_m_6.cpp"] = "test/BasicTest.cpp"
other_files["test_m_7.cpp"] = "test/BasicTest.cpp"
other_files["test_m_8.cpp"] = "test/BasicTest.cpp"
other_files["test_m_9.cpp"] = "test/BasicTest.cpp"
other_files["test_m_10.cpp"] = "test/BasicTest.cpp"
other_files["test_m_11.cpp"] = "test/BasicTest.cpp"
other_files["test_m_12.cpp"] = "test/BasicTest.cpp"


other_files["test_s_1.cpp"] = "test/BasicTest.cpp"
other_files["test_s_2.cpp"] = "test/BasicTest.cpp"
other_files["test_s_3.cpp"] = "test/BasicTest.cpp"
other_files["test_s_4.cpp"] = "test/BasicTest.cpp"
other_files["test_s_5.cpp"] = "test/BasicTest.cpp"

# submission files associated with the test files
sub_files = {}
sub_files["test_v_1.cpp"] = ""
sub_files["test_v_2.cpp"] = ""
sub_files["test_v_3.cpp"] = ""
sub_files["test_v_6.cpp"] = ""
sub_files["test_v_8.cpp"] = ""
sub_files["test_v_9.cpp"] = ""
sub_files["test_v_10.cpp"] = ""
sub_files["test_v_11.cpp"] = ""
sub_files["test_v_12.cpp"] = ""

sub_files["test_m_1.cpp"] = ""
sub_files["test_m_2.cpp"] = ""
sub_files["test_m_3.cpp"] = ""
sub_files["test_m_4.cpp"] = ""
sub_files["test_m_6.cpp"] = ""
sub_files["test_m_7.cpp"] = ""
sub_files["test_m_8.cpp"] = ""
sub_files["test_m_9.cpp"] = ""
sub_files["test_m_10.cpp"] = ""
sub_files["test_m_11.cpp"] = ""
sub_files["test_m_12.cpp"] = ""


sub_files["test_s_1.cpp"] = ""
sub_files["test_s_2.cpp"] = ""
sub_files["test_s_3.cpp"] = ""
sub_files["test_s_4.cpp"] = ""
sub_files["test_s_5.cpp"] = ""

compiler_lines = []
for test in test_files:
	compiler_lines.append( "clang++ -std=c++11 -o " + object_files[test] + " " + sub_files[test] + " " +
		other_files[test] + " " + "test/" + test + " ")
