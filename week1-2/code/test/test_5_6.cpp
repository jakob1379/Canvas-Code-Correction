#include "BasicTest.h"
#include "../5_6.h"

#include <iostream>
#include <math.h>

bool test_mm_1();
bool test_vm_1();
bool test_mv_1();
bool test_sm_1();
bool test_ms_1();

int main() {

	BasicTest test1("5_6 matrix matrix", "Test matrix * matrix", "test_5_6.cpp.result.txt", test_mm_1);
	BasicTest test2("5_6 vector matrix", "Test vector * matrix", "test_5_6.cpp.result.txt", test_vm_1);
	BasicTest test3("5_6 matrix vector", "Test matrix * vector", "test_5_6.cpp.result.txt", test_mv_1);
	BasicTest test4("5_6 scalar matrix", "Test scalar * matrix", "test_5_6.cpp.result.txt", test_sm_1);
	BasicTest test5("5_6 matrix scalar", "Test matrix * scalar", "test_5_6.cpp.result.txt", test_ms_1);

	test1.run();
	test2.run();
	test3.run();
	test4.run();
	test5.run();

	return 0;
}

bool test_ms_1() {
	double **b = new double*[3];
	for(int i = 0; i < 3; i++) {
		b[i] = new double[2];
	}

	double **res = new double*[3];
	for(int i = 0; i < 3; i++) {
		res[i] = new double[2];
	}

	res[0][0] = 0; res[0][1] = 0;
	res[1][0] = 0; res[1][1] = 0;

	b[0][0] = 1; b[0][1] = 2;
	b[1][0] = 3; b[1][1] = 4.1;
	b[2][0] = 3; b[2][1] = 4.1;

	Multiply(res, b, 2.1, 3, 2);

	bool res_return = 1;
	res_return = res_return && compareDouble(res[0][0],2.1,pow(10,-6));
	res_return = res_return && compareDouble(res[0][1],4.2,pow(10,-6));
	res_return = res_return && compareDouble(res[1][0],6.3,pow(10,-6));
	res_return = res_return && compareDouble(res[1][1],8.61,pow(10,-6));
	res_return = res_return && compareDouble(res[2][0],6.3,pow(10,-6));
	res_return = res_return && compareDouble(res[2][1],8.61,pow(10,-6));


	for(int i = 0; i < 3; i++) {
		delete[] b[i];
	}
	for(int i = 0; i < 3; i++) {
		delete[] res[i];
	}
	delete[] b;
	delete[] res;

	return res_return;	
}

bool test_sm_1() {
	double **b = new double*[3];
	for(int i = 0; i < 3; i++) {
		b[i] = new double[2];
	}

	double **res = new double*[3];
	for(int i = 0; i < 3; i++) {
		res[i] = new double[2];
	}

	res[0][0] = 0; res[0][1] = 0;
	res[1][0] = 0; res[1][1] = 0;

	b[0][0] = 1; b[0][1] = 2;
	b[1][0] = 3; b[1][1] = 4.1;
	b[2][0] = 3; b[2][1] = 4.1;

	Multiply(res, 2.1, b, 3, 2);

	bool res_return = 1;
	res_return = res_return && compareDouble(res[0][0],2.1,pow(10,-6));
	res_return = res_return && compareDouble(res[0][1],4.2,pow(10,-6));
	res_return = res_return && compareDouble(res[1][0],6.3,pow(10,-6));
	res_return = res_return && compareDouble(res[1][1],8.61,pow(10,-6));
	res_return = res_return && compareDouble(res[2][0],6.3,pow(10,-6));
	res_return = res_return && compareDouble(res[2][1],8.61,pow(10,-6));


	for(int i = 0; i < 3; i++) {
		delete[] b[i];
	}
	for(int i = 0; i < 3; i++) {
		delete[] res[i];
	}
	delete[] b;
	delete[] res;

	return res_return;
}

bool test_mv_1() {
	int brow = 3;
	int bcol = 2;
	double **b = new double*[brow];
	for(int i = 0; i < brow; i++)
		b[i] = new double[bcol];

	b[0][0] = 3; b[0][1] = 1;
	b[1][0] = 5; b[1][1] = 4.1;
	b[2][0] = 6; b[2][1] = 7;

	double *c = new double[2];
	c[0] = 6; c[1] = 2;
	double *res13 = new double[3];
	res13[0] = 0; res13[1] = 0; res13[2] = 0;

	Multiply(res13, b, c, brow, bcol, 2);


	bool res_return = compareDouble(res13[0], 20, pow(10,-6)) && compareDouble(res13[1], 38.2, pow(10,-6)) && compareDouble(res13[2], 50, pow(10,-6));

	for(int i = 0; i < brow; i++)
		delete b[i];
	delete[] res13;
	delete[] b;
	delete[] c;

	return res_return;
}

bool test_vm_1() {
	int brow = 3;
	int bcol = 2;
	double **b = new double*[brow];
	for(int i = 0; i < brow; i++)
		b[i] = new double[bcol];

	b[0][0] = 3; b[0][1] = 1;
	b[1][0] = 5; b[1][1] = 4.1;
	b[2][0] = 6; b[2][1] = 7;

	double *c = new double[3];
	c[0] = 6; c[1] = 2; c[2] = 10;
	double *res13 = new double[2];
	res13[0] = 0; res13[1] = 0;

	Multiply(res13, c, b, 3, brow, bcol);

	bool res_return = compareDouble(res13[0], 88, pow(10,-6)) && compareDouble(res13[1], 84.2, pow(10,-6));

	for(int i = 0; i < brow; i++)
		delete b[i];
	delete[] res13;
	delete[] b;
	delete[] c;

	return res_return;
}

bool test_mm_1() {
	int arow = 2;
	int acol = 3;
	int brow = acol;
	int bcol = 2;

	double **a = new double*[arow];
	for(int i = 0; i < arow; i++)
		a[i] = new double[acol];

	double **b = new double*[brow];
	for(int i = 0; i < brow; i++)
		b[i] = new double[bcol];

	double **res = new double*[arow];
	for(int i = 0; i < arow; i++) {
		res[i] = new double[bcol];
	}

	res[0][0] = 0; res[0][1] = 0;
	res[1][0] = 0; res[1][1] = 0;

	a[0][0] = 1.1; a[0][1] = 4; a[0][2] = 5;
	a[1][0] = 3; a[1][1] = 7; a[1][2] = 5;

	b[0][0] = 3; b[0][1] = 1;
	b[1][0] = 5; b[1][1] = 4.1;
	b[2][0] = 6; b[2][1] = 7;

	Multiply(res, a,b,arow,acol,brow,bcol);

	bool res_return = 1;
	res_return = res_return && compareDouble(res[0][0], 53.3, pow(10,-6));
	res_return = res_return && compareDouble(res[0][1], 52.5, pow(10,-6));
	res_return = res_return && compareDouble(res[1][0], 74.0, pow(10,-6));
	res_return = res_return && compareDouble(res[1][1], 66.7, pow(10,-6));

	// free
	for(int i = 0; i < arow; i++)
		delete a[i];

	for(int i = 0; i < brow; i++)
		delete b[i];

	for(int i = 0; i < arow; i++) {
		delete res[i];
	}

	delete[] res;
	delete[] a;
	delete[] b;

	return res_return;
}