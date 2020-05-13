#include "BasicTest.h"
#include <iostream>
#include "../Vector.hpp"
#include <typeinfo>

#include <math.h>


bool test();
bool test2();

int main() {
	BasicTest t1("Vector", "result", "test_v_12.cpp.result.txt",test);
	t1.run();
	
	return 0;
}

bool test() {
	Vector<double> v(2);
	v[0] = 5;
    v[1] = 4;
    float determ = v.CalculateNorm(3);
    std::cout << determ;
	return compareDouble(determ, 5.73879355, pow(10,-6));
}

