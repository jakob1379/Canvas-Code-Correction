#include <iostream>
#include "5_4.h"
#include <cmath>
#include <assert.h>

double calc_std(double a[], int length);

double calc_std(double a[], int length)
{
	assert(length >= 1);
	double std = 0;
	double sum = 0;
	double varians = 0;

	for (int j = 0; j < length; j++)
	{
		sum += a[j];
	}

	double mean = sum / length;

	if (length > 1)
	{
		for (int i = 0; i < length; i++)
		{
			varians += pow(a[i] - mean, 2);
		}

		varians = varians / (length - 1);
	}

	std = sqrt(varians);

	return std;
}

double calc_mean(double a[], int length);


double calc_mean(double a[], int length)
{
	assert(length >= 1);
	double summean = 0;

	if (length >= 1)
	{
		for (int i = 0; i < length; i++)
		{
			summean = summean + a[i];
		}
	}
	double mean = summean / length;

	return mean;
}

// Testing
//int main()
//{
//	double b[] = { 7, 10 };
//	std::cout << "std of given array is " << calc_std(b, 2);;
//	return 0;
//}