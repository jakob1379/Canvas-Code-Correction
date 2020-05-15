#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test1();

int main() {
	BasicTest t1("e 6.2_9", "test multiplication with a scalar", "test_6_2_9.cpp.result.txt",test1);
	t1.run();

	return 0;
}

bool test1() {
	Matrix2x2 m(1,2,3,4);
	m.MultScalar(2.5);

	return compareDouble(m.Getval00(),1*2.5,pow(10,-6)) && compareDouble(m.Getval01(),2*2.5,pow(10,-6)) &&
		   compareDouble(m.Getval10(),3*2.5,pow(10,-6)) && compareDouble(m.Getval11(),4*2.5,pow(10,-6));
}
