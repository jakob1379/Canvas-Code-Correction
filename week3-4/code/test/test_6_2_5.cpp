#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test1();
bool test2();

int main() {
	BasicTest t1("e 6.2_5", "test inverse of of [1,2;3,4.3]", "test_6_2_5.cpp.result.txt",test1);
	//BasicTest t2("e 6.2_5", "test inverse of of [1,1;2,2], should be [0,0;0,0] according to what was addtionally specified.", "test_6_2_5.cpp.result.txt",test2);
	t1.run();
	//t2.run();

	return 0;
}

bool test1() {
	Matrix2x2 m(1,2,3,4.3);
	Matrix2x2 minv = m.CalcInverse();

	return compareDouble(minv.Getval00(), -2.5294, pow(10,-4) ) && compareDouble(minv.Getval01(), 1.1765, pow(10,-4) ) &&
	       compareDouble(minv.Getval10(), 1.7647, pow(10,-4) ) && compareDouble(minv.Getval11(), -0.5882, pow(10,-4) );
}

bool test2() {
	Matrix2x2 m(1,1,2,2);
	Matrix2x2 minv = m.CalcInverse();
	return compareDouble(minv.Getval00(), 0, pow(10,-6) ) && compareDouble(minv.Getval01(), 0, pow(10,-6) ) &&
	       compareDouble(minv.Getval10(), 0, pow(10,-6) ) && compareDouble(minv.Getval11(), 0, pow(10,-6) );
}
