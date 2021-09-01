#include"5_3.h"

void swap_pointer(double *a, double *b)
{
    double a_holder = *a;
    *a = *b;
    *b = a_holder;
}
void swap_ref(double &a, double &b)
{
    double a_holder = a;
    a = b;
    b = a_holder;
}