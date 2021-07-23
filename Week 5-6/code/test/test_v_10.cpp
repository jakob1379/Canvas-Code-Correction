#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_10.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Vector", "types", "test_v_10.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Vector<float> v(2);
	v[0] = 5;
	Vector<float> v2(2);
	v2[1] = 10.2;

	Vector<float> v3 = v - v2;

	return compareDouble(v3[0], 5, pow(10,-6)) && compareDouble(v3[1],-10.2, pow(10,-6));
}

bool test2() {
	Vector<float> v(2);
	v[0] = 5;
	Vector<float> v2(2);
	v2[1] = 10.3;

	Vector<float> v3 = v - v2;

	return (typeid(v3[0]) == typeid(float)) && (typeid(v3[1]) == typeid(float));
}
