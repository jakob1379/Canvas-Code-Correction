#include <iostream>
#include <cmath>
#include"5_4.h"

double calc_mean(double a[], int length){
    double sum=0.0;
    for (int i=0; i<length; i++){
        sum += a[i];
    }
    double mean;
    mean=sum/length;
    return mean;
}


double calc_std(double a[], int length){
    double stdev=0.0;
    if (length == 1)
    {
        return 0;
    }
    else // length > 1
    {
        double m=calc_mean(a, length);
        // calculate the sum of all (x[i]-x_mean)^2, as in numerator for calculating st.dev
        double numerator=0.0;
        for (int i=0; i<length; i++){
            numerator += pow((a[i]-m), 2);
            stdev = sqrt(numerator/(length-1));
            return stdev;
        }
    } 
}