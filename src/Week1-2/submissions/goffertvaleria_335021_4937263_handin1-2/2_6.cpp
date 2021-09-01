#include <iostream>
#include <cmath>
#include"2_6.h"

double newton_Raphson(double initialGuess, double epsilon)
{
    double x_next=initialGuess, x_prev = initialGuess;
    bool terminate = false;
    while (!terminate){
        // x[i] = x[i-1] - f(x[i-1])/f'(x[i-1])
        x_next = x_prev - (exp(x_prev)+pow(x_prev,3)-5)/(exp(x_prev)+3*(pow(x_prev,2)));
        //std::cout << x_prev << "\t" << x_next << "\n";
        terminate = (fabs(x_next-x_prev) < epsilon);
        x_prev=x_next;
    }
    
    return  x_next;
}