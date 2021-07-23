#include "BasicTest.h"
#include "../Matrix2x2.hpp"

#include <iostream>

bool test1();
bool test2();

int main() {
	BasicTest t1("e 6.2_8", "test addition operator", "test_6_2_8.cpp.result.txt",test1);
	BasicTest t2("e 6.2_8", "test subtraction operator", "test_6_2_8.cpp.result.txt",test2);
	t1.run();
	t2.run();

	return 0;
}

bool test1() {
	Matrix2x2 m2(1,2,3,4);
	Matrix2x2 m1(5,6,7,8.5);
	Matrix2x2 m = m2 + m1;

	return compareDouble(m.Getval00(),1+5,pow(10,-6)) && compareDouble(m.Getval01(),2+6,pow(10,-6)) &&
		   compareDouble(m.Getval10(),3+7,pow(10,-6)) && compareDouble(m.Getval11(),4+8.5,pow(10,-6));
}

bool test2() {
	Matrix2x2 m2(1,2,3,4);
	Matrix2x2 m1(5,6,7,8.5);
	Matrix2x2 m = m2 - m1;

	return compareDouble(m.Getval00(),1-5,pow(10,-6)) && compareDouble(m.Getval01(),2-6,pow(10,-6)) &&
		   compareDouble(m.Getval10(),3-7,pow(10,-6)) && compareDouble(m.Getval11(),4-8.5,pow(10,-6));
}
