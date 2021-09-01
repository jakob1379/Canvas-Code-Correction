#include <iostream>
#include <cassert>
#include <string>
#include <cmath>
#include <fstream>
#include "5_10.h"

void swap_rows(int r1,int r2,double **A, int n){
	double d;
	for(int i=0;i<n;i++){
		d=A[r1][i];
		A[r1][i] = A[r2][i];
		A[r2][i] = d;
	}
}

void swap_rows_vector(int r1,int r2,double *b, int n){
	double d;
		d=b[r1];
		b[r1] = b[r2];
		b[r2] = d;
}

void pivot_funk(double **A, double *b, int n, int i){
	double epsilon = 0.0001;
		if(fabs(A[i][i]) <= epsilon){
			int max = i;
			for(int g=i+1;g<n;g++){
				if(fabs(A[g][i]) > A[max][i]){
					max = g;
				}
			}
			swap_rows(max, i, A,n);
			swap_rows_vector(max,i,b,n);
		}
	}

void guassian_elimination(double **A, double *b, double *u, int n){
	for(int i=0;i<n;i++){
		pivot_funk(A,b,n,i);
		double d = A[i][i];
		b[i] = b[i]/d;
		for(int g=i;g<n;g++){
			A[g][i] = A[g][i]/d;
		}
		for(int g=i+1;g<n;g++){
			pivot_funk(A,b,n,g);
			double d1 = A[g][i];
			b[g] -=d1*b[i];
			for(int k=0;k<n;k++){
				A[g][k]-=d1*A[i][k];
			}
		}
	}


	u[n-1]=b[n-1]/A[n-1][n-1];
	for(int g=n-2;g>=0;g--){
		double sum = b[g];
		for(int i=g+1;i<n;i++){
			sum -= A[g][i]*u[i];
		}
		u[g]=sum/A[g][g];
	}

}
