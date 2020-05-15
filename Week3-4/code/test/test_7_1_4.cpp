#include "BasicTest.h"
#include "../GraduateStudent.hpp"
#include <iostream>

bool test();

int main() {
	BasicTest t1("e 7.1.4", "test MoneyOwed method in GraduateStudent", "test_7_1_4.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	GraduateStudent s("casper",100.0,100.5, 0);

	return compareDouble(s.MoneyOwed(), 100.0, pow(10,-6));
}
