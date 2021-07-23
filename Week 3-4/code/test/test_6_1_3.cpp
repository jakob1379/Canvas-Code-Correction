#include "BasicTest.h"
#include "../ComplexNumber.hpp"
#include <iostream>

bool testcopy();

int main() {
	BasicTest t1("e 6.1.3", "test copy constructor", "test_6_1_3.cpp.result.txt",testcopy);
	t1.run();


	return 0;
}

bool testcopy() {
	ComplexNumber cn(5,6);
	ComplexNumber cn2 = cn;

	return compareDouble(cn.GetRealPart(), cn2.GetRealPart(),pow(10,-6)) && compareDouble(cn.GetImaginaryPart(), cn2.GetImaginaryPart(),pow(10,-6));
}
