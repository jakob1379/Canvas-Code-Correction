#include"5_9.h"
#include <iostream>
#include <cassert>

void solve3by3(double **A, double *b, double *u){
    // find determinant
    double det;
    det = A[0][0]*(A[1][1]*A[2][2]-A[2][1]*A[1][2]) - A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0]) + A[0][2]* (A[1][0]*A[2][1]-A[1][1]*A[2][0]);
    assert(det!=0);
    std::cout << det << "\n";

    // 1/det
    double det1 = 1/det;
    // find inverse of a matrix
    double invA[3][3];
    invA[0][0] = det1 * (A[1][1]*A[2][2] - A[2][1]*A[1][2]);
    invA[0][1] = det1 * (A[0][2]*A[2][1] - A[0][1]*A[2][2]);
    invA[0][2] = det1 * (A[0][1]*A[1][2] - A[0][2]*A[1][1]);
    invA[1][0] = det1 * (A[1][2]*A[2][0] - A[1][0]*A[2][2]);
    invA[1][1] = det1 * (A[0][0]*A[2][2] - A[0][2]*A[2][0]);
    invA[1][2] = det1 * (A[1][0]*A[0][2] - A[0][0]*A[1][2]);
    invA[2][0] = det1 * (A[1][0]*A[2][1] - A[2][0]*A[1][1]);
    invA[2][1] = det1 * (A[2][0]*A[0][1] - A[0][0]*A[2][1]);
    invA[2][2] = det1 * (A[0][0]*A[1][1] - A[1][0]*A[0][1]);

    // print invA
    // for (int i=0; i<3; i++) {
    //     for (int j=0; j<3; j++){
    //     std::cout << invA[i][j] << " ";
    //     if (j==2) {std::cout << "\n";}
    //     }
    // }

    // multiply invA and b
    double s=0;
    for (int i=0; i<3; i++) {
        for (int j=0; j<3; j++){
            s += invA[i][j]*b[j];
        }
        u[i]= s;
        s=0.0;
    }
}