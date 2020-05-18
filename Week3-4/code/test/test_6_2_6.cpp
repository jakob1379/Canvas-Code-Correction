#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test1();

int main() {
	BasicTest t1("e 6.2_6", "test assignment operator", "test_6_2_6.cpp.result.txt",test1);
	t1.run();

	return 0;
}

bool test1() {
	Matrix2x2 m(1,2,3,4);
	Matrix2x2 m1;
	m1 = m;

	return compareDouble(m.Getval00(),m1.Getval00(),pow(10,-6)) && compareDouble(m.Getval01(),m1.Getval01(),pow(10,-6)) &&
		   compareDouble(m.Getval10(),m1.Getval10(),pow(10,-6)) && compareDouble(m.Getval11(),m1.Getval11(),pow(10,-6));
}
