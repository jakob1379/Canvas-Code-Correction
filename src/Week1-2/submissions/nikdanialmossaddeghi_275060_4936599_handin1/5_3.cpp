#include <iostream>
#include "5_3.h"
#include <cmath>

void swap_pointer(double *a, double *b);

void swap_pointer(double* a, double* b)
{
	double r = *a;
	*a = *b;
	*b = r;
}

void swap_ref(double& a, double& b);

void swap_ref(double& a, double& b)
{
	double t = a;
	a = b;
	b = t;
}