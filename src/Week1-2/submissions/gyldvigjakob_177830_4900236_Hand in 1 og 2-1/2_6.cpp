#include <iostream>
#include <cmath>
#include <cassert>
#include "2_6.h"

double f (double x){
	return exp(x) + x*x*x - 5;
}

double fdiff (double x){
	return exp(x) + 3 * x*x;
}

double newton_Raphson(double initialGuess, double epsilon)
{
	double x_prev = initialGuess;
	double x_next = x_prev - f(x_prev)/fdiff(x_prev);

	while(fabs(x_prev-x_next) >= epsilon) {
		x_prev = x_next;
		x_next = x_prev - f(x_prev)/fdiff(x_prev);
	}

	return x_next;
}
