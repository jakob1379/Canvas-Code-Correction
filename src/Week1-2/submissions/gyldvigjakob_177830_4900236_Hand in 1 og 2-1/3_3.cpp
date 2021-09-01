#include <iostream>
#include <cmath>
#include <cassert>
#include <string>
#include <fstream>
#include "3_3.h"

void implicit_Euler(int n){
		assert(n > 1);
		double y[n-1];
		double x[n-1];
		double h = 1.0/(n-1);

		y[0] = 1;
		x[0] = 0;
		std::ofstream write_output("xy.dat");
		assert(write_output.is_open());
		for (int i=1; i<n-1; i++) {
			y[i] = y[i-1]/(1+h);
			x[i] = i*h;
			write_output << x[i] << "," << y[i] << "\n";
		}
		write_output.close();

		return;
};
