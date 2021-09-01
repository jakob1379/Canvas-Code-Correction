#include <iostream>
#include<cmath>
#include "5_10.h"

void guassian_elimination(double** A, double* b, double* u, int n);

void guassian_elimination(double** A, double* b, double* u, int n)
{
    //nest the b row onto the A matrix to use the gaussian elimination
    double** Sol;
    Sol = new double* [n];

    /*  for (int i = 0; i < n; i++)
      {
          Sol[i] = double[n + 1];
      }*/

    for (int i = 0; i < n; i++)
    {
        for (int j = 0; j < n; j++)
            Sol[i][j] = A[i][j];
    }

    for (int i = 0;i < n;i++)
    {
        Sol[i][n] = b[i];
    }


    //Pivots
    for (int i = 0; i < n; i++)
    {
        for (int k = i + 1; k < n; k++)
        {
            if (Sol[i][i] < Sol[k][i])
            {
                for (int j = 0; j < n + 1; j++)
                {
                    double tmp = Sol[i][j];
                    Sol[i][j] = Sol[k][j];
                    Sol[k][j] = tmp;
                }
            }
        }
    }

    //Eliminate variables 

    for (int i = 0; i < n - 1; i++)
    {
        for (int k = i + 1; k < n; k++)
        {
            double t = Sol[k][i] / Sol[i][i];
            for (int j = 0; j < n + 1; j++)
            {
                Sol[k][j] = Sol[k][j] - t * Sol[i][j];
            }
        }
    }

    //Write solutions to u

    for (int i = n - 1; i >= 0; i--)
    {
        u[i] = Sol[i][n];
        for (int k = 0; k < n; k++)
        {
            if (k != i)
            {
                u[i] = u[i] - Sol[i][k] * u[k];
            }
        }
    }

}



