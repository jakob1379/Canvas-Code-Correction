#include "BasicTest.h"
#include <iostream>
#include "../Matrix.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Matrix", "result", "test_m_1.cpp.result.txt",test);
	t1.run();
	
	BasicTest t2("Matrix", "types", "test_m_1.cpp.result.txt",test2);
	t2.run();

	return 0;
}

bool test() {
	Matrix<int> m(2,2);

	return compareDouble(m(0,0), 0, pow(10,-6)) && compareDouble(m(1,0), 0, pow(10,-6)) &&  
	       compareDouble(m(0,1), 0, pow(10,-6)) &&  compareDouble(m(1,1), 0, pow(10,-6));
}

bool test2() {
	Matrix<int> m(2,2);

	return (typeid(m(1,1)) == typeid(int));
}
