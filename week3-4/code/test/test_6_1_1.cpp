#include "BasicTest.h"
#include "../ComplexNumber.hpp"
#include <iostream>

bool testGetRealPart();
bool testGetImgPart();

int main() {
	BasicTest t1("e 6.1.1", "test GetRealPart", "test_6_1_1.cpp.result.txt",testGetRealPart);
	BasicTest t2("e 6.1.1", "test GetImaginaryPart", "test_6_1_1.cpp.result.txt",testGetImgPart);
	t1.run();
	t2.run();


	return 0;
}

bool testGetImgPart() {
	ComplexNumber cn(2,3);
	return compareDouble(cn.GetImaginaryPart(), 3, pow(10,-6));
}

bool testGetRealPart() {
	ComplexNumber cn(2,3);
	return compareDouble(cn.GetRealPart(), 2, pow(10,-6));
}
