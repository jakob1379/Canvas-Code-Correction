#include "BasicTest.h"
#include "../GraduateStudent.hpp"
#include <iostream>

bool test();

int main() {
	BasicTest t1("e 7.1.3", "test if GraduateStudent has a fullTime field", "test_7_1_3.cpp.result.txt",test);
	t1.run();


	return 0;
}

bool test() {
	GraduateStudent s("casper",100.0,100.5, 0);

	return s.fullTime == 0;
}
