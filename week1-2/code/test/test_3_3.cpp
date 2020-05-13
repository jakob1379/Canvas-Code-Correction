#include "../3_3.h"
#include <iostream>
#include "BasicTest.h"
#include <cmath>
#include "TA_3_3.h"
#include <fstream>

double precision = pow(10,-2);

bool test1();
bool test2();

// the test test for both length and correct solution at the same time.
int main(){
	BasicTest t1("e. 3_3", "Test against TA solution, n=100000", "test_3_3.cpp.result.txt", test1);
	t1.run();
	BasicTest t2("e. 3_3", "Test against TA solution, n=10000", "test_3_3.cpp.result.txt", test2);
	t2.run();
}

bool test1(){
	TA_implicit_Euler(100000);
	implicit_Euler(100000);

	std::ifstream infileTA("TA_xy.dat");
	std::ifstream infileStudent("xy.dat");
	double x, y, xTA, yTA;
	char tmp;
	bool toReturn = true;
	int counter = 0;
	while(infileStudent >> x >> tmp && counter < 10000){
		//std::cout << "tmp " << tmp;
		if ( tmp == ',') {
			infileStudent >> y;
		} else {
			y=1;
		}
		infileTA >> xTA >> tmp >> yTA;
		if(fabs(x-xTA)>precision || fabs(y-yTA)>precision){
			std::cout << "fail 1 ";
			toReturn = false;
			break;
		}
		//printf(":::::: %d\n",counter);
		counter +=1;
	}

	if (counter < 10000) {
		std::cout << "fail 1.5 ";
		toReturn = false;
	}
	//skal lige poppe fra TA solution os, mangler sidste linje her hvis while stoppede pga. eof.
	if(infileStudent.eof()){
		infileTA >> xTA >> tmp >> yTA;
	}

	if (infileStudent.eof() != infileTA.eof()){
		std::cout << "fail 2 ";
		//toReturn = false;
	}

	return toReturn;

}

bool test2(){
	TA_implicit_Euler(10000);
	implicit_Euler(10000);

	std::ifstream infileTA("TA_xy.dat");
	std::ifstream infileStudent("xy.dat");
	double x, y, xTA, yTA;
	char tmp;
	bool toReturn = true;
	int counter = 0;
	while(infileStudent >> x >> tmp && counter < 1000){
		if (  tmp == ',') {
			infileStudent >> y;
		} else {
			y=1;
		}
		infileTA >> xTA >> tmp >> yTA;
		if(fabs(x-xTA)>precision || fabs(y-yTA)>precision){
			std::cout << "fail 1 ";
			toReturn = false;
			break;
		}
		//printf("!!!!!! %d\n",counter);
		counter +=1;
	}

	if (counter < 1000) {
		std::cout << "fail 1.5";
		toReturn = false;
	}
	//skal lige poppe fra TA solution os, mangler sidste linje her hvis while stoppede pga. eof.
	if(infileStudent.eof()){
		infileTA >> xTA >> tmp >> yTA;
	}

	if (infileStudent.eof() != infileTA.eof()){
		std::cout << "fail 2 ";
		//toReturn = false;
	}

	return toReturn;
}

