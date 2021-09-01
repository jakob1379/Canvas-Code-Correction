#include "5_9.h"
#include <iostream>


double compute_3by3determinant(double **A) {
  double det = A[0][0] * ((A[1][1] * A[2][2]) - (A[1][2] * A[2][1]))
             - A[0][1] * ((A[1][0] * A[2][2]) - (A[1][2] * A[2][0]))
             + A[0][2] * ((A[1][0] * A[2][1]) - (A[1][1] * A[2][0]));

  return det;
}

double **get_adjcentMatrix(double **A, double *b, int adj, int n) {
  int i,j;
  double **adjA = new double *[n];
  for (i=0; i<n; i++) {
    adjA[i] = new double [n];
    for (j=0; j<n; j++){
      adjA[i][j] = A[i][j];
    }
  }
  switch(adj) {
  case 0:
    adjA[0][adj]=b[0];adjA[1][adj]=b[1];adjA[2][adj]=b[2];
  case 1:
    adjA[0][adj]=b[0];adjA[1][adj]=b[1];adjA[2][adj]=b[2];
  case 2:
    adjA[0][adj]=b[0];adjA[1][adj]=b[1];adjA[2][adj]=b[2];
  }
  return adjA;
}

void delete_matrix(double **A, int n) {
  for (int i=0; i<n; i++) {
    delete[] A[i];
  }
  delete[] A;
}

void solve3by3(double **A, double *b, double *u) {
  int n=3;

  double detA = compute_3by3determinant(A);

  double **A1 = get_adjcentMatrix(A,b,0,n);
  double detA1 = compute_3by3determinant(A1);

  double **A2 = get_adjcentMatrix(A,b,1,n);
  double detA2 = compute_3by3determinant(A2);

  double **A3 = get_adjcentMatrix(A,b,2,n);
  double detA3 = compute_3by3determinant(A3);

  delete_matrix(A1,n); delete_matrix(A2,n); delete_matrix(A3,n);

  u[0]=detA1/detA; u[1]=detA2/detA; u[2]=detA3/detA;
}