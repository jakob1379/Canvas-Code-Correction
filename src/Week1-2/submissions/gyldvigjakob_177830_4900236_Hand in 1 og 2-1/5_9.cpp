#include <iostream>
#include <cmath>
#include "5_9.h"

void solve3by3( double **A, double *b , double *u)
{
	double determinant=0.0;
	double A_inverse[3][3];

	for(int i=0; i<3; i++) {
		determinant += A[0][i] * (A[1][(i+1)%3] * A[2][(i+2)%3] - A[1][(i+2)%3] * A[2][(i+1)%3]);
	}

	for(int i=0; i<3; i++) {
		for(int j=0; j<3; j++) {
			A_inverse[i][j] = (A[(j+1)%3][(i+1)%3] * A[(j+2)%3][(i+2)%3] - A[(j+1)%3][(i+2)%3] * A[(j+2)%3][(i+1)%3])/ determinant;
		}
	}

	for (int i = 0; i<3; i++) {
		u[i] = A_inverse[i][0] * b[0] + A_inverse[i][1] * b[1] + A_inverse[i][2] * b[2];
	}

	return;

}
