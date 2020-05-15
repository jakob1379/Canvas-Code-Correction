#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test();

int main() {
	BasicTest t1("e 6.2_2", "test of 6.2.2", "test_6_2_2.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	Matrix2x2 m(1,2,3,4);
	Matrix2x2 m2 = m;

	return compareDouble(m.Getval00(), m2.Getval00(), pow(10,-6) ) &&
		   compareDouble(m.Getval10(), m2.Getval10(), pow(10,-6) ) &&
		   compareDouble(m.Getval01(), m2.Getval01(), pow(10,-6) ) &&
		   compareDouble(m.Getval11(), m2.Getval11(), pow(10,-6) );
}
