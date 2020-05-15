#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test();

int main() {
	BasicTest t1("e 6.2_1", "test of 6.2.1", "test_6_2_1.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	Matrix2x2 m;

	return m.Getval00() < pow(10,-6) && m.Getval01() < pow(10,-6) && m.Getval10() < pow(10,-6) && m.Getval11() < pow(10,-6);
}
