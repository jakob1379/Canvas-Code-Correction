#include <iostream>
#include <cmath>
#include "2_6.h"

double newton_Raphson(double initialGuess, double epsilon)
{
double x_prev = initialGuess;
double x_next = initialGuess - ((exp(initialGuess) + pow(initialGuess,3) -5)/(exp(initialGuess)+3*pow(initialGuess,2)));
while (abs(x_next-x_prev)>epsilon)
{
    x_prev = x_next;
    x_next = x_prev - ((exp(x_prev) + pow(x_prev,3) - 5 ) / (exp(x_prev)+3*pow(x_prev,2)));
}
return x_next;
}
