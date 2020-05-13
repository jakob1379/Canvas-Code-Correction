#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_6.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Vector", "types", "test_v_6.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Vector<double> v(2);
	v[0] = 5;
	Vector<double> v2 = v;
    v[0] = 1;

	return compareDouble(v2[0], 5, pow(10,-6)) && compareDouble(v[1],v2[1], pow(10,-6));
}

bool test2() {
	Vector<double> v(2);
	v[0] = 5;
	Vector<double> v2 = v;

	return (typeid(v[0]) == typeid(v2[0])) && (typeid(v[1]) == typeid(v2[1]));
}
