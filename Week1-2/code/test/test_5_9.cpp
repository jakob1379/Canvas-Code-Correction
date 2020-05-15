#include "../5_9.h"
#include <iostream>
#include "BasicTest.h"
#include <cmath>

double precision = pow(10,-4);

bool test1();
bool test2();
bool test3();

int main(){
	BasicTest t1("e 5_10","test lower triangle matrix", "test_5_9.cpp.result.txt",test1);
	t1.run();
	BasicTest t2("e 5_10","test 3x3 matrix", "test_5_9.cpp.result.txt",test2);
	t2.run();
}


bool test1(){
	int n = 3;
	double **testA = new double*[n];
	for(int i = 0; i<n; i++){
		testA[i] = new double[n];
	}
	testA[0][0] = 3; testA[0][1] = 0; testA[0][2] = 0;
	testA[1][0] = 2; testA[1][1] = 2; testA[1][2] = 0;
	testA[2][0] = 1; testA[2][1] = 1; testA[2][2] = 1;
	double testb[3] = {1,1,1};
	double testu[3];
	solve3by3(testA, testb,testu);
	//std::cout << testu[0] << " " << testu[1] << " " << testu[2] << std::endl;

	for(int i = 0; i<n; i++){
		delete [] testA[i];
	}
	delete [] testA;

	return (fabs(testu[0]-0.333333)<precision && fabs(testu[1]-0.166667)<precision && fabs(testu[2]-0.5)<precision);
}

bool test2(){
	int n = 3;
	double **testA = new double*[n];
	for(int i = 0; i<n; i++){
		testA[i] = new double[n];
	}
	testA[0][0] = 0; testA[0][1] = 1.5; testA[0][2] = -5;
	testA[1][0] = 7.5; testA[1][1] = 0; testA[1][2] = 0;
	testA[2][0] = 5; testA[2][1] = -3; testA[2][2] = 0;
	double testb[4] = {1,3.5,-2};
	double testu[4];
	solve3by3(testA, testb,testu);
	//std::cout << testu[0] << " " << testu[1] << " " << testu[2] << " " << testu[3] << std::endl;

	for(int i = 0; i<n; i++){
		delete [] testA[i];
	}
	delete [] testA;

	return (fabs(testu[0]-0.4667)<precision && fabs(testu[1]-1.4444)<precision && fabs(testu[2]-0.2333)<precision);

}