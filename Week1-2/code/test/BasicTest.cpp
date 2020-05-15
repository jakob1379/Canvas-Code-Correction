/*
 * BasicTest.cpp
 *
 *  Created on: Apr 3, 2015
 *      Author: casper
 */

#include "BasicTest.h"
#include <iostream>
#include <fstream>
#include <cassert>
#include <math.h>



bool compareDouble(double a, double b, double eps) {
	return fabs(a-b) < eps;
}


BasicTest::BasicTest(std::string n, std::string d, std::string path, bool (*f)()) {
	this->name = n;
	this->description = d;
	this->pathToResultFile = path;
	this->testFunction = f;
}

// seconds decide if the run should be time limitted
void BasicTest::run() {
	std::ofstream writer(pathToResultFile.c_str(), std::ios::app);
	assert(writer.is_open());


	writer << evaluate() << "\n";
	writer << name << ": " << description << "\n";



	writer.close();
}

std::string BasicTest::evaluate() {
	std::string result("");
	bool res = testFunction();
	if(res) {
		result += std::string("Passed");
	} else {
		result += std::string("Failed");
	}
	return result;
}



