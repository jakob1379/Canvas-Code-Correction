#include <iostream>
#include <cmath>
#include <cassert>
#include <string>
#include <fstream>
#include "5_6.h"

void Multiply(double **res, double **A, double **B, int ARows, int ACols, int BRows, int BCols)
{
	assert(ACols == BRows);
	for (int j=0; j<ARows; j++)
		for (int i=0; i<BCols; i++)
		{
			res[j][i]=0;
			for (int k=0; k<ACols; k++)
			{
				res[j][i] += A[j][k] * B[k][i];
			}
		}

		return;
};


void Multiply(double *res, double *A, double **B, int ACols, int BRows, int BCols)
{
		assert(ACols == BRows);
		for (int i=0; i<ACols; i++) {
			res[i]=0;
			for (int j=0; j<BRows; j++) {
				res[i] += A[j] * B[j][i];
			}
		}

		return;
}

void Multiply(double *res, double **A, double *B, int ARows, int ACols, int BRows) {
	assert(ACols == BRows);

	for (int i=0; i<ARows; i++) {
		res[i]=0;
		for (int j=0; j<BRows; j++) {
			res[i] += A[i][j] * B[j];
		}
	}

	return;
}

void Multiply(double **res, double scalar, double **B, int BRows, int BCols) {

		for (int i=0; i<BRows; i++) {
			for (int j=0; j<BCols; j++) {
				res[i][j] = scalar * B[i][j];
			}
		}

		return;
}

void Multiply(double **res, double **B, double scalar, int BRows, int BCols)
{
	for (int i=0; i<BRows; i++) {
		for (int j=0; j<BCols; j++) {
			res[i][j] = B[i][j] * scalar;
		}
	}

	return;
}
