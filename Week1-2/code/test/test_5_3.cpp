#include "BasicTest.h"
#include "../5_3.h"
#include <math.h>
bool test_swap_pointer();
bool test_swap_ref();

int main() {
	
	BasicTest test1("5_3 swap with pointer", "Test if two doubles are swapped using the pointer version", "test_5_3.cpp.result.txt", test_swap_pointer);
	test1.run();
	BasicTest test2("5_3 swap with pointer", "Test if two doubles are swapped using the reference version", "test_5_3.cpp.result.txt", test_swap_ref);
	test2.run();
	return 0;
}

bool test_swap_pointer() {
	double a = 5.3;
	double b = 10.5;

	double a_save = a;
	double b_save = b;

	swap_pointer(&a, &b);

	return (compareDouble(a,b_save, pow(10,-6)) && compareDouble(b,a_save, pow(10,-6)));
}

bool test_swap_ref() {
	double a = 5.3;
	double b = 10.5;

	double a_save = a;
	double b_save = b;

	swap_ref(a, b);

	return (compareDouble(a,b_save, pow(10,-6)) && compareDouble(b,a_save, pow(10,-6)));
}