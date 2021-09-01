#include <iostream>
#include <cassert>
#include <fstream>
#include "3_3.h"
using namespace std;
void implicit_Euler(int n) {

	assert(n > 1);

	//Stepsize
	double h = 1.0 / (n-1);

	//Initial x and y values
	double x = 0.0;
	double y = 1.0;

	//Open write output
	ofstream write_output ("xy.dat");
	assert(write_output.is_open());

	//Write initial values
	cout << x << "," << y << "\n";
	write_output << x << "," << y << "\n";

	//Iterate over number of steps; n-1
	for (int i = 0; i < n-1; i++)
	{
		y = y / (1+h);
		x = x + h;
		cout << x << "," << y << "\n";
		write_output << x << "," << y << "\n";
	}
	write_output.close();
}

//I'm not getting any prints to my xy.dat file,
//but I cannot see what's different from the examples given in the book.
//(output to console seems to work fine)