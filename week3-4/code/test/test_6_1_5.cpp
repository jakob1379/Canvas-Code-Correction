#include "BasicTest.h"
#include "../ComplexNumber.hpp"

bool test();

int main() {
	BasicTest t1("e 6.1.5", "test CalculateConjugate", "test_6_1_5.cpp.result.txt",test);
	t1.run();


	return 0;
}

bool test() {
	ComplexNumber cn(5,10);
	ComplexNumber cn2 = cn.CalculateConjugate();

	return compareDouble(cn.GetRealPart(), cn2.GetRealPart(),pow(10,-6)) && compareDouble(cn.GetImaginaryPart(), -cn2.GetImaginaryPart(),pow(10,-6));


}
