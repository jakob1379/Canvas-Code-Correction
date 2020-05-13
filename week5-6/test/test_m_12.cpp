#include "BasicTest.h"
#include <iostream>
#include "../Matrix.hpp"
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>
#include <vector>


bool test();
bool test2();

int main() {
	
	BasicTest t1("Matrix", "internal storage", "test_m_12.cpp.result.txt",test2);
	t1.run();

	return 0;
}


bool test2() {
	Matrix<int> m(2,2);
	m(0,0) = 5; m(0,1) = 1;
	m(1,0) = 2; m(1,1) = 3;

    std::vector<int> mRef = m.getStorage();

    return compareDouble(mRef[0], 5 , pow(10,-6)) && compareDouble(mRef[1], 1 , pow(10,-6)) && compareDouble(mRef[2], 2 , pow(10,-6)) && compareDouble(mRef[3], 3 , pow(10,-6));
    
}
