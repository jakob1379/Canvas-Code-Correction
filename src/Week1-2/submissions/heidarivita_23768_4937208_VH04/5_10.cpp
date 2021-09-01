#include <iostream>
#include <stdio.h>
#include <cstdlib>
#include "5_10.h"




// Matrix builder
double mat(int n)
{
    double** A = new double* [n];
     for (int i=0; i<n; i++)
     {
         A[i] = new double [n];
     }
    return **A;
}


// Gausee elimination
void guassian_elimination(double **A, double *b, double *u, int n)
{
    
    double temp; // for inside matirx
    
    // Gauss ellimination
    for (int i=1; i<=n-1; i++)
    {
        if (A[i][i] == 0.0)
        {
            std::cerr << "Error " << "\n";
            exit(0);
        }
        for (int j=i+1; j<=n; j++)
        {
            temp = A[j][i] / A[i][i];
            for (int k=1; k<=n+1; k++)
            {
                A[j][k] -= temp * A[i][k];
            }
        }
    }
    


    for (int i = n-1; i >= 1; i--)
    {
        u[n] = A[i][n+1];
        for (int j=i+1; j<=1; j++)
        {
            u[n] -= A[i][j] * u[n];
        }
        u[n] /= A[i][i];
    }
    

}








