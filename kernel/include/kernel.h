#ifndef AEGIS_KERNEL_H
#define AEGIS_KERNEL_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
  uint32_t process_ids[64];
  uint8_t priorities[64];
  uint8_t credits[64];
  uint32_t dispatch_counts[64];
  uint64_t enqueued_tick[64];
  uint64_t wait_ticks_total[64];
  uint64_t last_wait_latency[64];
  uint64_t total_dispatches;
  uint64_t scheduler_ticks;
  size_t high_watermark;
  uint32_t current_pid;
  uint32_t quantum_ticks;
  uint32_t quantum_remaining;
  size_t count;
  size_t head;
} aegis_scheduler_t;

typedef struct {
  size_t queue_depth;
  size_t high_watermark;
  uint64_t total_dispatches;
  uint64_t scheduler_ticks;
  uint32_t current_pid;
  uint32_t quantum_ticks;
  uint32_t quantum_remaining;
} aegis_scheduler_metrics_snapshot_t;

typedef enum {
  AEGIS_PRIORITY_LOW = 1,
  AEGIS_PRIORITY_NORMAL = 2,
  AEGIS_PRIORITY_HIGH = 3
} aegis_scheduler_priority_t;

int aegis_kernel_boot_check(void);
void aegis_scheduler_init(aegis_scheduler_t *scheduler);
int aegis_scheduler_add(aegis_scheduler_t *scheduler, uint32_t process_id);
int aegis_scheduler_add_with_priority(aegis_scheduler_t *scheduler, uint32_t process_id,
                                      uint8_t priority);
int aegis_scheduler_remove(aegis_scheduler_t *scheduler, uint32_t process_id);
int aegis_scheduler_set_priority(aegis_scheduler_t *scheduler, uint32_t process_id, uint8_t priority);
int aegis_scheduler_next(aegis_scheduler_t *scheduler, uint32_t *process_id);
size_t aegis_scheduler_count(const aegis_scheduler_t *scheduler);
uint64_t aegis_scheduler_total_dispatches(const aegis_scheduler_t *scheduler);
size_t aegis_scheduler_high_watermark(const aegis_scheduler_t *scheduler);
int aegis_scheduler_dispatch_count_for(const aegis_scheduler_t *scheduler, uint32_t process_id,
                                       uint32_t *dispatch_count);
void aegis_scheduler_reset_metrics(aegis_scheduler_t *scheduler);
void aegis_scheduler_set_quantum(aegis_scheduler_t *scheduler, uint32_t quantum_ticks);
int aegis_scheduler_on_tick(aegis_scheduler_t *scheduler, uint32_t *running_pid,
                            uint8_t *context_switch);
int aegis_scheduler_metrics_snapshot(const aegis_scheduler_t *scheduler,
                                     aegis_scheduler_metrics_snapshot_t *snapshot);
int aegis_scheduler_wait_ticks_for(const aegis_scheduler_t *scheduler, uint32_t process_id,
                                   uint64_t *wait_ticks);
int aegis_scheduler_last_latency_for(const aegis_scheduler_t *scheduler, uint32_t process_id,
                                     uint64_t *latency_ticks);

#endif
