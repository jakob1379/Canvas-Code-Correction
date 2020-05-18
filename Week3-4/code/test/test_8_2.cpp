#include "BasicTest.h"
#include "../Exercise82.hpp"
#include <iostream>

bool test();
bool test2();

int main() {
	BasicTest t1("e 8.2", "test CalcAbs function for double", "test_8_2.cpp.result.txt",test);
	t1.run();

	BasicTest t2("e 8.2", "test CalcAbs function for int", "test_8_2.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	double v1 = -1.2;
	double v2 = 1.2;
	return compareDouble( CalcAbs(v1), 1.2, pow(10,-6)) && compareDouble( CalcAbs(v2), 1.2, pow(10,-6)) ;
}

bool test2() {
	int v1 = -1;
	int v2 = 2;
	return CalcAbs(v1) == 1 && CalcAbs(v2) == 2;
}
