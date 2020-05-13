#include "BasicTest.h"
#include <iostream>
#include "../Matrix.hpp"
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>

bool test();
bool test2();

int main() {
	BasicTest t1("Matrix", "result", "test_m_10.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Matrix", "types", "test_m_10.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {

	Matrix<int> m(2,2);
	m(0,0) = 5; m(0,1) = 1;
	m(1,0) = 2; m(1,1) = 3;

	Vector<int> v(2);
	v[0] = 6;
	v[1] = 2;

	Vector<int> v1 = m * v;

	return compareDouble(v1[0], 32, pow(10,-6)) && compareDouble(v1[1], 18, pow(10,-6));
}

bool test2() {
	Matrix<int> m(2,2);
	m(0,0) = 5; m(0,1) = 1;
	m(1,0) = 2; m(1,1) = 3;

	Vector<int> v(2);
	v[0] = 6;
	v[1] = 2;

	Vector<int> v1 = m * v;

	return (typeid(v1[0]) == typeid(int));
}
