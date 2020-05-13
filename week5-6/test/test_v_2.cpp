#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_2.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Vector", "types", "test_v_2.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Vector<int> v2(2);
	Vector<int> v(v2);
    v2[0] = 1;

	return compareDouble(v[0], 0, pow(10,-6)) && compareDouble(v[1],0, pow(10,-6));
}

bool test2() {
	Vector<int> v2(5);
	Vector<int> v(v2);
	return (typeid(int) == typeid(v[0])) && (typeid(int) == typeid(v2[3]));
}
