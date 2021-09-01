#include <stdio.h>
#include "5_9.h"
#include <iostream>
#include <cstdlib>

double determinant(double M[3][3])
{
    // Equation from exercise 5.8 for
    double det;
    det = M[0][0] * (M[1][1] * M[2][2] - M[2][1] * M[1][2])
        - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
        + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]);
    return det;
}

void solve3by3(double **A, double *b, double *u)
{
    // cramer's rule: Matrix d
    double d[3][3] = {
        { A[0][0], A[0][1], A[0][2] },
        { A[1][0], A[1][1], A[1][2] },
        { A[2][0], A[2][1], A[2][2] },
    };


    // cramer's rule: Matrix d1
    double d1[3][3] = {
        { b[0], A[0][1], A[0][2] },
        { b[1], A[1][1], A[1][2] },
        { b[2], A[2][1], A[2][2] },
    };

    // cramer's rule: Matrix d2
    double d2[3][3] = {
        { A[0][0], b[0], A[0][2] },
        { A[1][0], b[1], A[1][2] },
        { A[2][0], b[2], A[2][2] },
    };

    // cramer's rule: Matrix d3
    double d3[3][3] = {
        { A[0][0], A[0][1], b[0] },
        { A[1][0], A[1][1], b[1] },
        { A[2][0], A[2][1], b[2] },
    };

    // cramer's rule - A is nonsingular.
    double D  = determinant(d );
    double D1 = determinant(d1);
    double D2 = determinant(d2);
    double D3 = determinant(d3);
    
    u[0] = D1 / D;
    u[1] = D2 / D;
    u[2] = D3 / D;
}




