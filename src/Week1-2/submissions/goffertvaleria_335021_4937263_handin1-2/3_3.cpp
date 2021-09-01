#include <iostream>
#include <cassert>
#include <fstream> // to write a file
#include <cstdlib>
#include"3_3.h"

void implicit_Euler(int n){
    assert(n>1);
    std::ofstream write_file("xy.dat");
    assert(write_file.is_open());
    double h = 1.0/((double)n-1); // step size h on the interval 0 <= x <= 1 
    double x = 0.0, y_prev = 1.0, y_next;
    for (int i=1; i<=n; i++){
        y_next = y_prev/(1+h);
        write_file << x << "," << y_prev << "\n";
        y_prev = y_next;
        x = ((double)i)*h;
    }
    write_file.close();
}