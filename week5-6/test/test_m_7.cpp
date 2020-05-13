#include "BasicTest.h"
#include <iostream>
#include "../Matrix.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Matrix", "result", "test_m_7.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Matrix", "types", "test_m_7.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Matrix<float> m1(2,2);
	m1(1,1) = 5.5;
	Matrix<float> m2(2,2);
	m2(0,0) = 1.2;

	Matrix<float> m = m1 + m2;

	return compareDouble(m(0,0), 1.2, pow(10,-6)) && compareDouble(m(0,1), 0, pow(10,-6)) &&  
	       compareDouble(m(1,0), 0, pow(10,-6)) &&  compareDouble(m(1,1), 5.5, pow(10,-6));
}

bool test2() {
	Matrix<float> m1(2,2);
	m1(1,1) = 5.5;
	Matrix<float> m2(2,2);
	m2(0,0) = 1.2;

	Matrix<float> m = m1 + m2;

	return (typeid(m(1,1)) == typeid(float));
}
