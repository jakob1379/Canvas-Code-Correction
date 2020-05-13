#include "BasicTest.h"
#include "../Student.hpp"
#include <iostream>

bool test();

int main() {
	BasicTest t1("e 7.1.1", "test of public member variables name and tuition_fees", "test_7_1_1.cpp.result.txt",test);
	t1.run();


	return 0;
}

bool test() {
	Student s("casper",100.0,100.5);

	return !s.name.compare("casper") && compareDouble(s.tuition_fees, 100.5, pow(10,-6));
}
