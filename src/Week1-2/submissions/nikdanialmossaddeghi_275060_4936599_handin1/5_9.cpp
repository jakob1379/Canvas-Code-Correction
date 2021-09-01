#include "5_9.h"
#include <assert.h>
#include <iostream>

void solve3by3(double** A, double* b, double* u);

void solve3by3(double** A, double* b, double* u)
{
    //standard way of getting determinant for 3x3 matrix
    double determinant = A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
        - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
        + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);

    //determine non-singularity i.e. matrix inverse exists
    assert(determinant != 0);

    //using cramer's rule we get the determinant of d0, d1, and d2. These are 3x3 matrices, so we use the same method as above.
    //the b row is the coefficients row
    double detd0 = b[0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1])
        - A[0][1] * (b[1] * A[2][2] - A[1][2] * b[2])
        + A[0][2] * (b[1] * A[2][1] - A[1][1] * b[2]);

    double detd1= A[0][0] * (b[1] * A[2][2] - A[1][2] * b[2])
        - b[0] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
        + A[0][2] * (A[1][0] * b[2] - b[1] * A[2][0]);

    double detd2=A[0][0] * (A[1][1] * b[2] - b[1] * A[2][1])
        - A[0][1] * (A[1][0] * b[2] - b[1] * A[2][0])
        + b[0] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);

    // the solution for the linear system is the determinants divided by the original 3x3 determinant
    u[0] = detd0 / determinant;
    u[1] = detd1 / determinant;
    u[2] = detd2 / determinant;

}

