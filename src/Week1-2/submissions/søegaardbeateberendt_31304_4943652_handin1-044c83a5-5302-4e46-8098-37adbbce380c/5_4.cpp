#include "5_4.h"
#include <iostream>
#include <math.h>


double calc_std(double a[], int length) {
  double sigma, mu;
  int i;
  if (length < 1) {
    printf("error - length < 2\n");
    return 0;
  }
  else if (length == 1) {
    return 0;
  }
  else {
    mu = calc_mean(a, length);
    for (i=0; i<length; i++) {
      sigma += pow((a[i] - mu),2);
    }
  }
  return sqrt(sigma/(length-1));
}

double calc_mean(double a[], int length) {
  double mu;
  int i;
  if (length < 1) {
    printf("error - length < 2\n");
    return 0;
  }
  for (i=0; i<length; i++) {
    mu += a[i];
  }
  return mu/length;
}