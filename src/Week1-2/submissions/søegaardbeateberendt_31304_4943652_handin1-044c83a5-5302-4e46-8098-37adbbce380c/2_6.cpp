#include "2_6.h"
#include <iostream>
#include <math.h>


double f(double x) {
  return exp(x) + pow(x,3) - 5.0;
}

double fp(double x) {
  return exp(x) + 3.0 * pow(x,2.0);
}

double newton_Raphson(double initialGuess, double epsilon) {
  double x_next, x_prev, dir;
  bool run = true;
  int maxiter, i;
  x_prev = initialGuess; //too long var name >:(
  x_next = x_prev;
  maxiter = 100;
  i = 0;

  while (run) {
    printf("iterations %d -- x=%f -- f(x)=%f\n", i, x_next,f(x_next));
    i+=1;
    x_next = x_prev - ((double) f(x_prev))/((double) fp(x_prev));

    if (fabs(x_next - x_prev) < epsilon) {
      printf("solution after %d iterations is \n", i);
      run = false;
    }

    x_prev = x_next;

    maxiter -= 1;
    if (maxiter == 0) {
      printf("max iterations has been reached\n");
      run = false;
    }
  }
  return x_next;
}