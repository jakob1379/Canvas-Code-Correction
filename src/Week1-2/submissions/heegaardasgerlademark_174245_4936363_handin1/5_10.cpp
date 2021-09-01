#include <iostream>
#include "5_10.h"
#include <cmath>
#include <cassert>
#include <fstream>
using namespace std;
void guassian_elimination(double** A, double* b, double* u, int n) {
	double temp;
	int length = sizeof(b);
	for (int i = 0; i < length; i++)
	{
//Pivot (if necessary);
		for (int p = i; p < length; p++)
		{
			if (A[p][i]>A[i][i])
			{
				for (int q = i; q < length; q++)
				{
					temp = A[i][q];
					A[i][q] = A[p][q];
					A[p][q] = temp;
					temp = b[q];
					b[q] = b[p];
					b[p] = temp;
				}
			}
		}
//Forward Elimination;
//Normalize current column
		b[i] = b[i] / A[i][i];
		for (int j = i; j < length; j++)
		{
			A[i][j] = A[i][j] / A[i][i];
		}
//Eliminate Below current diagonal element
		for (int k = min(length, i+1); k < length; k++)
		{
			for (int l = i; l < length; l++)
			{
				A[k][l] = A[k][l] - A[k][i] * A[i][l];
			}
			b[k] -= A[k][i] * b[i];
		}
//Backward Substitution;
		for (int i = length; i > 0; i--)
		{
			for (int j = i-1; j > 0; j--)
			{
				b[j] -= A[j][i] * b[i];
			}
		}
//Insert result into solution;
		for (int i = 0; i < length; i++)
		{
			u[i] = b[i];
		}
	}
}