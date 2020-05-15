#include "../2_6.h"
#include <iostream>
#include "BasicTest.h"
#include <cmath>

double precision = pow(10,-4);
bool test1();

int main(){
	BasicTest t1("e 2_6", "initial guess 0, epsilon 0.0001", "test_2_6.cpp.result.txt",test1);
	t1.run();
}

bool test1(){
	double solution = newton_Raphson(0,0.0001);
	//std::cout << solution << std::endl;
	return (fabs(solution-1.19367) < precision);
}