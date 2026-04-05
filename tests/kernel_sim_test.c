#include <stdio.h>
#include "kernel.h"

static int test_kernel_boot(void) {
  if (aegis_kernel_boot_check() != 0) {
    fprintf(stderr, "kernel boot check failed\n");
    return 1;
  }
  return 0;
}

static int test_scheduler_round_robin(void) {
  aegis_scheduler_t scheduler;
  uint32_t pid = 0;
  aegis_scheduler_init(&scheduler);

  if (aegis_scheduler_add(&scheduler, 1001u) != 0 ||
      aegis_scheduler_add(&scheduler, 1002u) != 0 ||
      aegis_scheduler_add(&scheduler, 1003u) != 0) {
    fprintf(stderr, "scheduler add failed\n");
    return 1;
  }
  if (aegis_scheduler_count(&scheduler) != 3u) {
    fprintf(stderr, "scheduler count mismatch\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1001u) {
    fprintf(stderr, "expected pid 1001\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1002u) {
    fprintf(stderr, "expected pid 1002\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1003u) {
    fprintf(stderr, "expected pid 1003\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1001u) {
    fprintf(stderr, "expected pid 1001 after wrap\n");
    return 1;
  }
  return 0;
}

static int test_scheduler_remove(void) {
  aegis_scheduler_t scheduler;
  uint32_t pid = 0;
  aegis_scheduler_init(&scheduler);
  if (aegis_scheduler_add(&scheduler, 1u) != 0 ||
      aegis_scheduler_add(&scheduler, 2u) != 0 ||
      aegis_scheduler_add(&scheduler, 3u) != 0) {
    fprintf(stderr, "scheduler add failed in remove test\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1u) {
    fprintf(stderr, "remove test expected initial pid 1\n");
    return 1;
  }
  if (aegis_scheduler_remove(&scheduler, 2u) != 0) {
    fprintf(stderr, "remove pid 2 failed\n");
    return 1;
  }
  if (aegis_scheduler_count(&scheduler) != 2u) {
    fprintf(stderr, "scheduler count after remove mismatch\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 3u) {
    fprintf(stderr, "expected pid 3 after removing 2\n");
    return 1;
  }
  if (aegis_scheduler_next(&scheduler, &pid) != 0 || pid != 1u) {
    fprintf(stderr, "expected pid 1 after wrap in remove test\n");
    return 1;
  }
  return 0;
}

int main(void) {
  if (test_kernel_boot() != 0) {
    return 1;
  }
  if (test_scheduler_round_robin() != 0) {
    return 1;
  }
  if (test_scheduler_remove() != 0) {
    return 1;
  }
  puts("kernel simulation check passed");
  return 0;
}
