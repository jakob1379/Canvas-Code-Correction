#include "BasicTest.h"
#include "../5_4.h"

#include <iostream>
#include <math.h>

bool test_mean_multiple();
bool test_mean_one();

bool test_std_multiple();
bool test_std_one();

int main() {
	BasicTest test1("5_4 mean multiple values", "Test mean of [1,2,3,4,5]", "test_5_4.cpp.result.txt", test_mean_multiple);
	test1.run();

	BasicTest test2("5_4 mean single value", "Test mean of [5]", "test_5_4.cpp.result.txt", test_mean_one);
	test2.run();

	BasicTest test3("5_4 std multiple values", "Test std of [1,2,3,4,5]", "test_5_4.cpp.result.txt", test_std_multiple);
	test3.run();

	BasicTest test4("5_4 std multiple values", "Test std of [5]", "test_5_4.cpp.result.txt", test_std_one);
	test4.run();
}

bool test_mean_multiple() {
	double arr[5] = {1,2,3,4,5};
	double mean = calc_mean(arr, 5);
	return compareDouble(mean, 3, pow(10,-6));
}

bool test_mean_one() {
	double arr[1] = {5};
	double mean = calc_mean(arr, 1);
	return compareDouble(mean, 5, pow(10,-6));
}

bool test_std_multiple() {
	double arr[5] = {1,2,3,4,5};
	double std = calc_std(arr, 5);
	return compareDouble(std, 1.5811, pow(10,-3));
}

bool test_std_one() {
	double arr[1] = {5};
	double std = calc_std(arr, 1);
	return compareDouble(std, 0, pow(10,-6));
}

