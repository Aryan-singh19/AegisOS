#include "kernel.h"

#define AEGIS_SCHEDULER_CAPACITY 64u

int aegis_kernel_boot_check(void) {
  return 0;
}

void aegis_scheduler_init(aegis_scheduler_t *scheduler) {
  if (scheduler == 0) {
    return;
  }
  scheduler->count = 0;
  scheduler->head = 0;
}

static int find_index(const aegis_scheduler_t *scheduler, uint32_t process_id, size_t *index) {
  size_t i;
  if (scheduler == 0 || index == 0 || process_id == 0) {
    return 0;
  }
  for (i = 0; i < scheduler->count; ++i) {
    if (scheduler->process_ids[i] == process_id) {
      *index = i;
      return 1;
    }
  }
  return 0;
}

int aegis_scheduler_add(aegis_scheduler_t *scheduler, uint32_t process_id) {
  size_t existing = 0;
  if (scheduler == 0 || process_id == 0) {
    return -1;
  }
  if (scheduler->count >= AEGIS_SCHEDULER_CAPACITY) {
    return -1;
  }
  if (find_index(scheduler, process_id, &existing)) {
    return -1;
  }
  scheduler->process_ids[scheduler->count] = process_id;
  scheduler->count += 1;
  return 0;
}

int aegis_scheduler_remove(aegis_scheduler_t *scheduler, uint32_t process_id) {
  size_t idx = 0;
  size_t i;
  if (!find_index(scheduler, process_id, &idx)) {
    return -1;
  }
  for (i = idx + 1; i < scheduler->count; ++i) {
    scheduler->process_ids[i - 1] = scheduler->process_ids[i];
  }
  scheduler->count -= 1;
  if (scheduler->count == 0) {
    scheduler->head = 0;
    return 0;
  }
  if (idx < scheduler->head && scheduler->head > 0) {
    scheduler->head -= 1;
  } else if (scheduler->head >= scheduler->count) {
    scheduler->head = 0;
  }
  return 0;
}

int aegis_scheduler_next(aegis_scheduler_t *scheduler, uint32_t *process_id) {
  if (scheduler == 0 || process_id == 0 || scheduler->count == 0) {
    return -1;
  }
  *process_id = scheduler->process_ids[scheduler->head];
  scheduler->head = (scheduler->head + 1) % scheduler->count;
  return 0;
}

size_t aegis_scheduler_count(const aegis_scheduler_t *scheduler) {
  if (scheduler == 0) {
    return 0;
  }
  return scheduler->count;
}
