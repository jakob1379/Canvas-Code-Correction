#include <cassert>
#include"5_6.h"

void Multiply(double **res, double **A, double **B, int ARows, int ACols, int BRows, int BCols){
    assert(ACols==BRows);
    double s=0;
    for (int i=0; i<ARows; i++) {
        for (int j=0; j<BRows; j++) {
            for (int k=0; k<BRows; k++){
                s += A[i][k]*B[k][j];
            }
            res[i][j]= s;
            s=0.0;
        }
    }
}


void Multiply(double *res, double *A, double **B, int ACols, int BRows, int BCols){
    assert(ACols==BRows);
    double s=0;
    for (int i=0; i<ACols; i++) {
        for (int j=0; j<BRows; j++){
            s += A[j]*B[j][i];
        }
        res[i]= s;
        s=0.0;
    }
}

void Multiply(double *res, double **A, double *B, int ARows, int ACols, int BRows){
    assert(ACols==BRows);
    double s=0;
    for (int i=0; i<ARows; i++) {
        for (int j=0; j<BRows; j++){
            s += A[i][j]*B[j];
        }
        res[i]= s;
        s=0.0;
    }
}


void Multiply(double **res, double **B, double scalar, int BRows, int BCols){
    for (int i=0; i<BRows; i++) {
        for (int j=0; j<BCols; j++){
            res[i][j] = scalar * B[i][j];
        }
    }
}


void Multiply(double **res, double scalar, double **B, int BRows, int BCols){
    for (int i=0; i<BRows; i++) {
        for (int j=0; j<BCols; j++){
            res[i][j] = B[i][j] * scalar;
        }
    }
}