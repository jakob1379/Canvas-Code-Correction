#include "5_10.h"
#include <iostream>
#include <math.h>

void guassian_elimination(double **A, double *b, 
                          double *u, int n) {
  /*
   i used this pdf called gaussian_elim.pdf, that i found floating in space
   but instead of splitting the elimination up bewteen A and b I used an 
   augmented matrix U instead to do it all at once. 
  */

  double U[n][n+1], max_val, tmp0, tmp1, res;
  int i,j,k,max_idx;

  // augmented matrix 
  // U[row][col]
  for (i=0; i<n; i++) {
    U[i][n] = b[i];
    for (j=0; j<n; j++) {
      U[i][j] = A[i][j];
    }
  }

  //guassian elimination with partial pivoting
  max_val = 0.0;
  max_idx = 0;
  // for (k=0; k<n; k++) {
  // k = column
  for (k=0; k<n-1; k++) {
    // k - start

    // find max index -> if ik > k 
    // i = row
    for (i=k; i<n; i++) {
      if (fabs(U[i][k])>max_val) {
        max_val = fabs(U[i][k]); // get the max value in the row of column k
        max_idx = i;             // get the index of said value
      }
    }
    
    // swap rows
    // and if we aren't on the diagonal then swap
    if (max_idx!=k) {
      // max_idx/k = row; j = column
      for (j=k; j<n+1; j++) {
        tmp0 = U[max_idx][j];         // tmp val holder for current max value
        U[max_idx][j] = U[k][j];      // swap values so that max value 
        U[k][j] = tmp0;               // set 
      }
    }
    
    // elimination 
    /*
    U(i,j) = U(i,j) - sum_{i=k+1}^{n}(U(i,k)/U(k,k))
    */
    for (i=k+1; i<n; i++) {
      tmp1 = -U[i][k]/U[k][k]; // the sum part
      for (j=k; j<n+1; j++) {
        U[i][j] += tmp1*U[k][j];
      }
    }
  } // k - end

  // get the solution by backward substitution
  /*
  u[i] = U(i,n) - sum_{n-1}^{0}(U(i,j)*u(j))/U(i,i)
  */
  for (i=n-1; i>=0; i--) {
    res = U[i][n];
    for (j=i+1; j<n; j++) {
      res -= U[i][j]*u[j];
    }
    u[i] = res / U[i][i];
  }
}