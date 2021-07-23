#include "BasicTest.h"
#include "../ComplexNumber.hpp"

bool test();

int main() {
	BasicTest t1("e 6.1.6", "test SetConjugate", "test_6_1_6.cpp.result.txt",test);
	t1.run();


	return 0;
}

bool test() {
	ComplexNumber cn(2,7);
	cn.SetConjugate();
	return cn.GetRealPart() == 2 && cn.GetImaginaryPart() == -7;

	return compareDouble(cn.GetRealPart(), 2,pow(10,-6)) && compareDouble(cn.GetImaginaryPart(), -7,pow(10,-6));
}
