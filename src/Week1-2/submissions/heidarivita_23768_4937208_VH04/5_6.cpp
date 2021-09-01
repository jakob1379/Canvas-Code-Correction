#include "5_6.h"
#include <iostream>
#include <cstdlib>
#include <assert.h>


// Matrix * Matrix
void Multiply(double **res, double **A, double **B, int ARows, int ACols, int BRows, int BCols)
{
    assert(ACols==BRows);
    for (int i = 0; i < ARows; i++){
        for (int j = 0; j < BCols; j++) {
            res[i][j] = 0.0;
            for (int k = 0; k < ACols; k++) {
                res[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}


// H-Vector * Matrix
void Multiply(double *res, double *A, double **B, int ACols, int BRows, int BCols)
{
    assert(ACols==BRows);
    for (int j = 0; j < BCols; j++) {
        res[j] = 0.0;
        for (int k = 0; k < ACols; k++) {
            res[j] += A[k] * B[k][j];
        }
    }
}

// Matrix * V-Vector
void Multiply(double *res, double **A, double *B, int ARows, int ACols, int BRows)
{
    assert(ACols==BRows);
    for (int j = 0; j < ARows; j++) {
        res[j] = 0.0;
        for (int k = 0; k < ACols; k++) {
            res[j] += A[j][k] * B[k];
        }
    }
}

// Scalar * Matrix
void Multiply(double **res, double scalar, double **B, int BRows, int BCols)
{
    for (int i = 0; i < BRows; i++){
        for (int j = 0; j < BCols; j++) {
            res[i][j] = 0.0;
            res[i][j] = scalar * B[i][j];
        }
    }
}


// Matrix * Scalar
void Multiply(double **res, double **B, double scalar, int BRows, int BCols)
{
    Multiply(res, scalar, B, BRows, BCols);
}

