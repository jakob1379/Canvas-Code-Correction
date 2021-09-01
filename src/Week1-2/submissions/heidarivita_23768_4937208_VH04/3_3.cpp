#include <stdio.h>
#include <iostream>
#include <fstream>  //
#include <cmath>
#include <cassert>
#include "3_3.h"

void implicit_Euler(int n)
{
//    std::cout << "i " << std::endl;   // Debug
    assert(n > 1);
    //Defining arrays x and y of size n specified by the user:
    double x = 0.0;
    double y = 1.0;
    double h = 1.0/n;
    std::ofstream objvar("xy.dat");
    assert(objvar.is_open());
    objvar << x << ' ' << y << "\n";
    
    for (int i=0; i<n-1 ; i++)
    {
        objvar << (x += h) << ' ' << (y *= (1.0 / (1.0 + h))) << "\n";
        std::cout << x << ' ' << y << "\n";
    }
    objvar.close();
}


