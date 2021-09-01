#include "5_4.h"
#include <iostream>
#include <cmath>
#include <cassert>

double calc_mean(double a[], int length)
{
    double *sum  = new double;
    double *mean = new double;

    *sum = 0.0;
    *mean = 0.0;
    assert(length > 1);  //This halts the codechecker!??
    
    for (int i = 0; i < length; i++)
    {
        *sum += a[i];
    }
    *mean = *sum/length;
    
    delete sum;   // avoid memory leak
    delete mean;  //
    
    return *mean;
}

double calc_std(double a[], int length)
{
    double *sum = new double;
    double *mean = new double;
    
    *sum = 0.0;
    *mean = calc_mean(a, length);
    for(int i = 0; i < length; i++)
    {
        *sum += pow(a[i] - *mean, 2);
    }
    
    delete sum;   // avoid memory leak
    delete mean;  //
    
    return sqrt(*sum/(length - 1));
}
