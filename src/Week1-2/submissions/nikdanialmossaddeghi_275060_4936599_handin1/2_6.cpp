#include <iostream>
#include <cmath>
#include "2_6.h"

double newton_Raphson(double initialGuess, double epsilon)
{
	double x_prev = initialGuess;
	double x_next = x_prev- (exp(x_prev) + pow(x_prev, 3) - 5)/exp(x_prev) + 3 * pow(x_prev, 2);
	
	for (int i = 1; i < 100; i++)
	{
		while (fabs(x_prev - x_next) > epsilon)
		{
			x_prev = x_next;
			x_next = x_prev - (exp(x_prev) + pow((x_prev), 3) - 5)
				/ (exp((x_prev)) + 3 * pow(x_prev, 2));
		}
	}

	return x_next;
}
