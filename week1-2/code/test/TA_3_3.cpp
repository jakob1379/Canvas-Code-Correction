/*
 * 5_10.cpp
 *
 *  Created on: Apr 3, 2015
 *      Author: Christian
 */

#include "TA_3_3.h"
#include <iostream>
#include <fstream>
#include <cmath>

/*
int main() {
	TA_implicit_Euler(pow(10,-5),pow(10,6));
}
*/

void TA_implicit_Euler(int n){
	double h = 1.0/n;
	double y = 1;
	std::ofstream myfile;
	myfile.open("TA_xy.dat");
	for(int i = 0; i<n; i++){
		myfile << h*i << "," << y << "\n";
		y = y/(1+h);
	}

	myfile.close();
}
