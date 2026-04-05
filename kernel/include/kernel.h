#ifndef AEGIS_KERNEL_H
#define AEGIS_KERNEL_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
  uint32_t process_ids[64];
  size_t count;
  size_t head;
} aegis_scheduler_t;

int aegis_kernel_boot_check(void);
void aegis_scheduler_init(aegis_scheduler_t *scheduler);
int aegis_scheduler_add(aegis_scheduler_t *scheduler, uint32_t process_id);
int aegis_scheduler_remove(aegis_scheduler_t *scheduler, uint32_t process_id);
int aegis_scheduler_next(aegis_scheduler_t *scheduler, uint32_t *process_id);
size_t aegis_scheduler_count(const aegis_scheduler_t *scheduler);

#endif
