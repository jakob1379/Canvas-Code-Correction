#include "BasicTest.h"
#include "../ComplexNumber.hpp"
#include <iostream>

bool testRealPart();
bool testImgPart();

int main() {
	BasicTest t1("e 6.1.2", "test RealPart", "test_6_1_2.cpp.result.txt",testRealPart);
	BasicTest t2("e 6.1.2", "test ImaginaryPart", "test_6_1_2.cpp.result.txt",testImgPart);
	t1.run();
	t2.run();


	return 0;
}

bool testImgPart() {
	ComplexNumber cn(2,3.3);
	return compareDouble(ImaginaryPart(cn), 3.3, pow(10,-6));
}

bool testRealPart() {
	ComplexNumber cn(2,3);
	return compareDouble(RealPart(cn), 2, pow(10,-6));
}
