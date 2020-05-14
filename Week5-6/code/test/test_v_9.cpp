#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_9.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Vector", "types", "test_v_9.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Vector<double> v(2);
	v[0] = 5;
	Vector<double> v2(2);
	v2[1] = 10;

	Vector<double> v3 = v + v2;

	return compareDouble(v3[0], 5, pow(10,-6)) && compareDouble(v3[1],10, pow(10,-6));
}

bool test2() {
	Vector<double> v(2);
	v[0] = 5;
	Vector<double> v2(2);
	v2[1] = 10;

	Vector<double> v3 = v + v2;

	return (typeid(v3[0]) == typeid(double)) && (typeid(v3[1]) == typeid(double));
}
