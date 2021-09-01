#include <iostream>
#include "5_9.h"
#include <cmath>
#include <cassert>
#include <fstream>
using namespace std;
void solve3by3(double** A, double* b, double* u) {
	double detA =
		A[0][0] * (A[1][1] * A[2][2] - A[2][1] * A[1][2])
		- A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
		+ A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);

	double detA_0 = 
		b[0] * (A[1][1] * A[2][2] - A[2][1] * A[1][2])
		- A[0][1] * (b[1] * A[2][2] - A[1][2] * b[2])
		+ A[0][2] * (b[1] * A[2][1] - A[1][1] * b[2]);
	u[0] = detA_0 / detA;
	double detA_1 =
		A[0][0] * (b[1] * A[2][2] - b[2] * A[1][2])
		- b[0] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
		+ A[0][2] * (A[1][0] * b[2] - b[1] * A[2][0]);
	u[1] = detA_1 / detA;
	double detA_2 =
		A[0][0] * (A[1][1] * b[2] - A[2][1] * b[1])
		- A[0][1] * (A[1][0] * b[2] - b[1] * A[2][0])
		+ b[0] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
	u[2] = detA_2 / detA;
}