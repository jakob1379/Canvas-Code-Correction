#include <iostream>
#include <cmath>
#include <cassert>
#include <string>
#include <fstream>
#include "5_3.h"

void swap_pointer(double *a, double *b){
	double c = *a;
	*a = *b;
	*b = c;

}

void swap_ref(double &a, double &b){
	double c = a;
	a = b;
	b = c;
}
