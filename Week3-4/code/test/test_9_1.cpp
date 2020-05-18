#include "BasicTest.h"
#include "../OutOfRangeException.hpp"
#include "../FileNotOpenException.hpp"
#include <iostream>

bool test();
bool test2();

int main() {
	BasicTest t1("e 9.1", "test OutOfRangeException", "test_9_1.cpp.result.txt",test);
	t1.run();
	BasicTest t2("e 9.1", "test FileNotOpenException", "test_9_1.cpp.result.txt",test2);
	t2.run();
	
	return 0;
}

bool test() {
	try {
		throw OutOfRangeException("beskrivelse lalalalala");
	} catch(OutOfRangeException &err) {
		return 1;
	}
	return 0;

}

bool test2() {
	try {
		throw FileNotOpenException("beskrivelse igen");
	} catch(FileNotOpenException &err) {
		return 1;
	}
	return 0;
}
