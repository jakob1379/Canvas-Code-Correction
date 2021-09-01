#include <iostream>
#include <cmath>
#include <cassert>
#include <string>
#include <fstream>
#include "5_4.h"

double calc_mean(double a[], int length){
	double sum = 0.0;

	for(int i=0; i<length; i++) {
		sum += a[i];
	}

	return sum/length;
}

double calc_std(double a[], int length) {
	double sigma = 0.0;
	double average = 0.0;

	if(length > 1) {
		average = calc_mean(a, length);
		
		for(int i=0; i<length; i++) {
			sigma += (a[i] - average)*(a[i] - average);
		}

		sigma = sqrt(sigma/(length-1));
	}

    return sigma;
}
