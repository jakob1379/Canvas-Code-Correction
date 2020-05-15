#include "BasicTest.h"
#include "../PhdStudent.hpp"
#include <iostream>

bool test();

int main() {
	BasicTest t1("e 7.1.5", "test MoneyOwed method in PhdStudent (should just be 0)", "test_7_1_5.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	PhdStudent s("casper",100.0,100.5, 0);

	return compareDouble(s.MoneyOwed(), 0, pow(10,-6));
}
