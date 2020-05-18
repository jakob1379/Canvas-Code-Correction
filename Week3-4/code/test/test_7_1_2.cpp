#include "BasicTest.h"
#include "../Student.hpp"
#include <iostream>

bool test();

int main() {
	BasicTest t1("e 7.1.2", "test of SetLibraryFines and GetLibraryFines", "test_7_1_2.cpp.result.txt",test);
	t1.run();

	return 0;
}

bool test() {
	Student s("casper",100.0,100.5);
	s.SetLibraryFines(-100);

	Student s1("casper",100.0,100.5);
	s1.SetLibraryFines(1.0);;

	return compareDouble(s.GetLibraryFines(), 100.0, pow(10,-6)) && compareDouble(s1.GetLibraryFines(), 1.0, pow(10,-6));
}

