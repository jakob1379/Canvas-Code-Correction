#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_3.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Vector", "types", "test_v_3.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Vector<double> v(2);
	v[0] = 5;

	return compareDouble(v[0], 5, pow(10,-6)) && compareDouble(v[1],0, pow(10,-6));
}

bool test2() {
	Vector<double> v(2);
	v[0] = 5;

	return (typeid(v[0]) == typeid(double)) && (typeid(v[1]) == typeid(double));
}
