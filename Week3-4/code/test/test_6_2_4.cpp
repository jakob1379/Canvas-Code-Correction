#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test();

int main() {
	BasicTest t1("e 6.2_4", "test CalcDeterminant of [1,2.5;3,0.01]", "test_6_2_4.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	Matrix2x2 m(1,2.5,3,0.01);
	double det = m.CalcDeterminant();
	return compareDouble(det, -7.49, pow(10,-6)); 
}
