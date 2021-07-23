#include "BasicTest.h"
#include "../ComplexNumber.hpp"


bool test();

int main() {
	BasicTest t1("e 6.1.4", "test of 6.1.4", "test_6_1_4.cpp.result.txt",test);
	t1.run();


	return 0;
}

bool test() {
	ComplexNumber cn(4.2);

	return compareDouble(cn.GetRealPart(),4.2,pow(10,-6)) && compareDouble(cn.GetImaginaryPart(), 0,pow(10,-6));
}
