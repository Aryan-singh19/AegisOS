#include <stdio.h>
#include "kernel.h"

int main(void) {
  if (aegis_kernel_boot_check() != 0) {
    fprintf(stderr, "kernel boot check failed\n");
    return 1;
  }
  puts("kernel simulation check passed");
  return 0;
}
