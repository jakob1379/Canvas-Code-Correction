#include "BasicTest.h"
#include "../CalculateExponential.hpp"
#include "../ComplexNumber.hpp"
bool test3x3diagonal();

int main() {
	BasicTest t1("e 6.1.7", "test of CalculateExponential with (2+3i),(4+5i),(6+7i) in the diagonal of a 3x3 matrix with nMax=50", "test_6_1_7.cpp.result.txt",test3x3diagonal);
	t1.run();

	return 0;
}

bool test3x3diagonal() {
	ComplexNumber **arr = new ComplexNumber*[3];
	arr[0] = new ComplexNumber[3];
	arr[1] = new ComplexNumber[3];
	arr[2] = new ComplexNumber[3];

	arr[0][0] = ComplexNumber(2,3);
	arr[1][1] = ComplexNumber(4,5);
	arr[2][2] = ComplexNumber(6,7);

	ComplexNumber** res = new ComplexNumber*[3];
	res[0] = new ComplexNumber[3];
	res[1] = new ComplexNumber[3];
	res[2] = new ComplexNumber[3];
	res[0][0] = ComplexNumber(0,0); res[0][1] = ComplexNumber(0,0); res[0][2] = ComplexNumber(0,0);
	res[1][0] = ComplexNumber(0,0); res[1][1] = ComplexNumber(0,0); res[1][2] = ComplexNumber(0,0);
	res[2][0] = ComplexNumber(0,0); res[2][1] = ComplexNumber(0,0); res[2][2] = ComplexNumber(0,0);

	CalculateExponential(arr, 50, res);

	bool bres = 1;
	bres = bres && compareDouble(res[0][0].GetRealPart(), -7.3151, pow(10,-4)) && compareDouble(res[0][0].GetImaginaryPart(), 1.0427, pow(10,-4));
	bres = bres && compareDouble(res[1][1].GetRealPart(), 15.4874, pow(10,-4)) && compareDouble(res[1][1].GetImaginaryPart(), -52.3555, pow(10,-4));
	bres = bres && compareDouble(res[2][2].GetRealPart(), 304.1459, pow(10,-2)) && compareDouble(res[2][2].GetImaginaryPart(), 265.0473, pow(10,-2));

	delete[] res[0]; delete[] res[1]; delete[] res[2];
	delete[] res;

	delete[] arr[0]; delete[] arr[1]; delete[] arr[2];
	delete[] arr;

	return bres;

}
