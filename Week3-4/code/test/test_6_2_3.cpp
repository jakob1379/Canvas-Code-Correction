#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test();

int main() {
	BasicTest t1("e 6.2_3", "test of 6.2.3", "test_6_2_3.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	Matrix2x2 m(1,2,3,4);

	return compareDouble(m.Getval00(), 1, pow(10,-6) ) &&
		   compareDouble(m.Getval10(), 3, pow(10,-6) ) &&
		   compareDouble(m.Getval01(), 2, pow(10,-6) ) &&
		   compareDouble(m.Getval11(), 4, pow(10,-6) );
}
