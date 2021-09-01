#include <iostream>
#include "3_3.h"
#include <assert.h>
#include <fstream>
#include <cmath>

void implicit_Euler(int n);


void implicit_Euler(int n)
{
	std::ofstream write_output("xy.dat");
	assert(write_output.is_open());
	assert(n > 1);


	double y[n];
	y[0] = (double) 1;

	double x[n];
	x[0] = (double) 0; //siden n=0 og 0*h=0

	//find stepsize:
	double h = 1 / (n - 1);

	// find x[n]s
	for (int i = 1; i < n; i++)
	{
		x[i] = h * (double) i;
	}

	// find y[n]s
	// initial formula -y[n] = (y[n] - y[n - 1]) / h but we isolate for nonnegative
	for (int k = 1; k < n; k++)
	{
		y[k] = y[k - 1] / (2 * h);
	}

	// write to txt
	for (int j = 0; j < n; j++)
	{
		write_output << x[j] << "," << y[j] << "\n";
	}

	write_output.close();
}

