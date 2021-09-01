#include "5_6.h"
#include <iostream>


void Multiply(double **res, double **A, double **B, 
              int ARows, int ACols, int BRows, 
              int BCols) {
  /*
  0. multiply a matrix and matrix of given sizes
  ok!
  */
  int i,j,k;
  if (ARows == BCols && BRows == ACols) {
    for (i=0; i<ARows; i++) {
      for (j=0; j<BCols; j++) {
        res[i][j] = 0.0;
        for (k=0; k<ACols; k++) {
          res[i][j] += A[i][k]*B[k][j]; 
        }
      }
    }
  } else if (ACols == BRows) {
    for (i=0; i<ARows; i++) {
      for (j=0; j<BCols; j++) {
        res[i][j] = 0.0;
        for (k=0; k<ACols; k++) {
          res[i][j] += A[i][k]*B[k][j];          
        }
      }
    } 
  } else if (BCols == ARows) {
      for (i=0; i<BRows; i++) {
        for (j=0; j<ACols; j++) {
          res[i][j] = 0.0;
          for (k=0; k<BCols; k++) {
            res[i][j] += A[k][j]*B[i][k];          
        }
      }
    }
  } else {
    std::cout << "error rows don't align" << std::endl;
  }
}


void Multiply(double *res, double *A, double **B, 
              int ACols, int BRows, int BCols) {
  /*
  1. multiply a vector,A, and matrix,B, of given sizes
  [1, 2] x [2, 2] -> [1,2]

  [1 2] x [1 2] -> [1 2]
          [3 4]
  ok!
  */
  int i, j;
  // match vector cols with matrix rows
  if (ACols == BRows) {
    for (i=0; i<BRows; i++) {
      res[i] = 0.0;
      for (j=0; j<ACols; j++){
        res[i] += A[j]*B[j][i];
      }
    }
  } 
}

void Multiply(double *res, double **A, double *B, 
              int ARows, int ACols, int BRows) {
  /*
  ARows = 2
  ACols = 3
  BRows = 3

  A = | a b c |
      | d e f |

  b = | a |
      | b |
      | c |

  i = ARows; j = ACols
  i,j = 0,0 -> a*a
  i,j = 0,1 -> b*b
  i,j = 0,2 -> c*c
  i,j = 1,0 -> d*a
  i,j = 1,1 -> e*b
  i,j = 1,2 -> f*c

  2. multiply a matrix, A, and a vector,B, of given size
  [2,2] x [2,1] -> [2,1]

  [1 2] x [1] -> [1]
  [3 4]   [2]    [2]
  ok  
  */
  int i, j;
  // match matrix cols with vector rows
  if (ACols == BRows) {
    for (i=0; i<ARows; i++) {
      res[i] = 0.0;
      for (j=0; j<ACols; j++){
        res[i] += A[i][j]*B[j];
      }
    }
  } 
}

void Multiply(double **res, double scalar, double **B, 
              int BRows, int BCols) {
  /*
  3. multiply a scalar, s, and matrix, B, of a given size
  ok!
  */
  int i,j;
  for (i=0; i<BRows; i++) {
    for (j=0; j<BCols; j++) {
      res[i][j] = scalar*B[i][j];
    }
  }
}

void Multiply(double **res, double **B, double scalar, 
              int BRows, int BCols) {
  /*
  4. multiply a matrix and scalar of a given size
  ok!
  */
  int i,j;
  for (i=0; i<BRows; i++) {
    for (j=0; j<BCols; j++) {
      res[i][j] = B[i][j]*scalar;
    }
  }
}