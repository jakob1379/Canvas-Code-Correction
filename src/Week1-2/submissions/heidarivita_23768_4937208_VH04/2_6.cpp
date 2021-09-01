
#include <stdio.h>
#include <iostream>
#include <cassert>
#include <cmath>

#include "2_6.h"





double newton_Raphson(double initialGuess, double epsilon)
{
    double x[100];
    int i = 1;     //
    x[0] = initialGuess;
    for (; i < 100; i++)
    {
//        std::cout << i << std::endl;  // debug
        x[i] = x[i-1] - (exp(x[i-1]) + pow(x[i-1], 3) - 5) / (exp(x[i-1]) + 3*pow(x[i-1], 2));
//        std::cout << "i = "<< i << std::endl; //
        if (fabs(x[i] - x[i-1]) < epsilon)
        {
            break;
        }
    }
//    std::cout << i << std::endl; // debug
    return x[i];
}
       
    
    














