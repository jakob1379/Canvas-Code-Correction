#include <iostream>
#include "5_4.h"
#include <cmath>
using namespace std;

double calc_std(double a[], int length) {
	double mean = calc_mean(a, length);
	double sum = 0;
	if (length == 1)
	{
		cout << "Input only contained one number, thus standard deviation cannot be calculated";
		return 0;
	}
	for (int i = 0; i < length; i++)
	{
		sum += pow(a[i] - mean, 2);
	}
	double StdDev = sum/(length-1);
	StdDev = sqrt(StdDev);
	return StdDev;
}

double calc_mean(double a[], int length) {
	double sum = 0;
	for (int i = 0; i < length; i++)
	{
		sum += a[i];
	}
	sum = sum / length;
	return sum;
}