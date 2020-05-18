#include "BasicTest.h"
#include <iostream>
#include "../Matrix.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Matrix", "result", "test_m_2.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Matrix", "types", "test_m_2.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Matrix<float> m2(2,2);
	m2(0,0) = 324.431;
	Matrix<float> m(m2);

	return compareDouble(m(0,0), 324.431, pow(10,-6)) && compareDouble(m(1,0), 0, pow(10,-6)) &&  
	       compareDouble(m(0,1), 0, pow(10,-6)) &&  compareDouble(m(1,1), 0, pow(10,-6));
}

bool test2() {
	Matrix<float> m2(2,2);
	m2(1,1) = 324.431;
	Matrix<float> m(m2);

	return (typeid(m(1,1)) == typeid(float));
}
