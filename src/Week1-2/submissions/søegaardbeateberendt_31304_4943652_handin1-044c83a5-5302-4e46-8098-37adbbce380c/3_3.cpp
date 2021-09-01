#include "3_3.h"
#include <cassert>
#include <iostream>
#include <fstream>


double f(double x, double y) {
  return -y;
}

void implicit_Euler(int n) {
  double y[n], x[n], yp, h;

  assert(n > 1);
  h = 1 / (n-1.0);

  y[0] = 1;
  x[0] = 0;
  
  std::ofstream result;
  result.open("tmp.dat");
  if (!result.is_open()) {
    std::cout << "tmp.dat" << "dosen't exit. making one now!" << std::endl; 
    result.open("tmp.dat", std::ios::out|std::ios::in|std::ios::trunc);
  }
  else {
    for (int i=0; i<n; i++) {
      x[i+1] = x[i] + h;
      yp = f(x[i]+h, y[i]);
      y[i+1] = y[i] + h*((yp)/(1+h));
      result << x[i] << "," << y[i] << std::endl;
    }
  }
  result.close();
  remove("xy.dat");
  rename("tmp.dat", "xy.dat");
}