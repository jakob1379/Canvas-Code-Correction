#include "BasicTest.h"
#include "../FowardEulerSolver.hpp"
#include <iostream>
#include <fstream>

bool test_actual_result();
bool test_file();

double f(double y, double t) {
	return 1 + t;
}

int main() {
	BasicTest t1("e 7.3.2", "test return value of FowardEulerSolver with y0=2, h=0.00001, interval=0,1", "test_7_3_2.cpp.result.txt",test_actual_result);
	t1.run();

	//BasicTest t2("e 7.3.2", "test file created by FowardEulerSolver with y0=2, h=0.00001, interval=0,1", "test_7_3_2.cpp.result.txt",test_file);
	//t2.run();

	return 0;
}

bool test_actual_result() {
	FowardEulerSolver euler(&f);
	euler.SetInitialValue(2);
	euler.SetStepSize(0.00001);
	euler.SetTimeInterval(0,1);

	double t = 0.9999999;
	//std::cout << euler.SolveEquation() - (t*t + 2*t + 4)/2 << " <-----\n";
	return compareDouble(euler.SolveEquation(), (t*t + 2*t + 4)/2, pow(10,-2));
}

bool test_file() {
	std::ifstream TA("test/TA_forwardeuler.dat");
	std::ifstream student("forwardeuler.dat");

	if(student.fail()) { // it is indeed fail
		return 0;
	}

	bool res = 1;

	double TA_t;
	double TA_y;
	double t;
	double y;
	char tmp;
	while(student >> t >> tmp >> y && (tmp == ',')){
		TA >> TA_t >> tmp >> TA_y;
		if( !(compareDouble(TA_t, t, pow(10,-3)) && compareDouble(TA_y, y, pow(10,-3))) ) {
			res = 0;
		}
	}

	//when the while loop ends, the TA file is one behind...
	if(student.eof()){
		TA >> TA_t >> tmp >> TA_y;
	}

	if( student.eof() != TA.eof() ) {
		res = 0;
	}


	TA.close();
	student.close();

	return res;	
}
