#include <stdio.h>
#include <iostream>
#include "5_3.h"

void swap_pointer(double *a, double *b)
{
    double *tmp = new double;
    *tmp = *a;
    *a = *b;
    *b = *tmp;
    delete tmp;  // to avoid memory leak
}

void swap_ref(double &a, double &b)
{
    double tmp;
    tmp = a;
    a = b;
    b = tmp;
}


