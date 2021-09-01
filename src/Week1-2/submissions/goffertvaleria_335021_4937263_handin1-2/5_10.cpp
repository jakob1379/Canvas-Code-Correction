#include <iostream>
#include <cassert>
#include <algorithm>
#include"5_10.h"

void row_pivoting(double **A, double *b, int c, int n);
void Multiply(double **res, double **A, double **B, int Rows, int Cols);
void Multiply(double *res, double *A, double **B, int ACols, int BRows, int BCols);


void guassian_elimination(double **A, double *b, double *u, int n){
    assert(sizeof(A)==sizeof(A[0])); 
    for (int c=0; c<n-1; c++){ // c stands for columns
        // pivot at each step
        row_pivoting(A,b,c,n);
        
        // ---------- checking how pivoting goes ----------
        // ------------------------------------------------
        // std::cout << "step " << c << " pivoted a:\n";
        // for (int i=0; i<n; i++) {
        //     for (int j=0; j<n; j++){
        //     std::cout << A[i][j] << " ";
        //     if (j==n-1) {std::cout << "\n";}
        //     }
        // }
        // std::cout << "\n";
        // std::cout << "pivoted b: ";
        // for (int i=0; i<n; i++) {
        //     std::cout << b[i] << " ";
        // }
        // std::cout << "\n";
        // --------------------------------------------------

        // elimination process
        for (int i=c+1; i<n; i++){
            //if (A[i][c] == 0){continue;}
            double factor = A[c][c]/A[i][c];
            for (int j=c; j<n; j++){
                A[i][j] = A[c][j] - A[i][j]*factor;
            }
            b[i] = b[c] - b[i]*factor;

        // --------- checking how elimination goes ---------
        // std::cout << "step " << c << " a with eliminated column:\n";
        // for (int i=0; i<n; i++) {
        //     for (int j=0; j<n; j++){
        //     std::cout << A[i][j] << " ";
        //     if (j==n-1) {std::cout << "\n";}
        //     }
        // }
        // std::cout << "b: ";
        // for (int i=0;i<n;i++){
        //     std::cout << b[i] << " ";
        // }
        // std::cout << "\n";
        // --------------------------------------------------
    }
    }

    // back substitution
    // find last unknown first: u[n]
    u[n-1]=b[n-1]/A[n-1][n-1];
    // u[0]...u[n-1] unknowns
    double *s= new double;
    for (int i=n-2; i>=0; i--){
        *s=0.0;
        for (int j=i+1; j<n; j++){
            *s += A[i][j]*u[j];
        }
        u[i] = (b[i]-*s) / A[i][i];
    }
    delete s;
}

void row_pivoting(double **A, double *b, int c, int n){
    //c - index of current column
    //
    // get a list of values col in a current column c by iterating 
    // over remaining rows of the column (starting from i'th row)
    
    // temporary holders for A and b while they're undertaking change
    double **pivotedA = new double* [n];
    for (int i=0; i<n; i++){
        pivotedA[i]=new double [n];
    }
    double *pivotedb = new double [n];
    
    // current column values
    double col[n-c];
    for (int l=0; l<n-c; l++){
        col[l]=A[c+l][c];
    }

    // ---------- check if we look at right column ----------
    // std::cout << "\ncol:\n";
    // for (int l=0;l<n-c;l++){
    //     std::cout << col[l] << " ";
    // }
    // -------------------------------------------------------

    // find max value in the column and the index of its row
    double row_w_highest_value_i;
    row_w_highest_value_i = std::max_element(col, col + (n-c)) - col + c;
    
    // ---------- checking ----------
    // std::cout << "\nrow with highest value: " << row_w_highest_value_i << "\n";
    
    
    // create P matrix for row pivoting
    double **P = new double* [n];
    for (int i=0; i<n; i++){
        P[i]=new double [n];
    }
    for (int l=0; l<n; l++){
        for (int k=0; k<n; k++){
            if (l==k && l!=row_w_highest_value_i && l!=c){
                P[l][k]=1;
            }
            else if (l==row_w_highest_value_i && k==c){
                P[l][k]=1;
            }
            else if ((l==c && k==row_w_highest_value_i)){
                P[l][k]=1;
            }
            else{
                P[l][k]=0;
            }
        }
    }
    // --------------------------------------------------
    // ---------------- printing P out ------------------
    // std::cout << "\nP:\n";
    // for (int l=0; l<4; l++) {
    //     for (int k=0; k<4; k++){
    //         std::cout << P[l][k] << " ";
    //         if (k==3) {std::cout << "\n";}
    //     }
    // }
    // --------------------------------------------------

    
    // let's pivot now

    // 1) P*A matrix-matrix multiplication
    Multiply(pivotedA,P,A,n,n);
    // 2) P*b matrix-vector multiplication
    Multiply(pivotedb,b,P,n,n,n);
    
    // replace A with pivoted A and b with pivoted b
    for (int l=0; l<n; l++) {
        for (int k=0; k<n; k++){
            A[l][k]=pivotedA[l][k];
        }
        b[l]=pivotedb[l];
    }

    // freeing up space
    for (int i=0; i<n; i++){
        delete[] P[i];
        delete[] pivotedA[i];
    }
    delete[] P;
    delete[] pivotedA;
    delete[] pivotedb;
}


void Multiply(double **res, double **A, double **B, int Rows, int Cols){
    assert(Rows==Cols);
    double s=0;
    for (int i=0; i<Cols; i++) {
        for (int j=0; j<Rows; j++) {
            for (int k=0; k<Cols; k++){
                s += B[k][j]*A[i][k];
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