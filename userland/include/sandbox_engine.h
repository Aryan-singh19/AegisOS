#ifndef AEGIS_SANDBOX_ENGINE_H
#define AEGIS_SANDBOX_ENGINE_H

#include <stddef.h>
#include <stdint.h>

#include "capability.h"
#include "sandbox_policy.h"

typedef enum {
  AEGIS_ACTION_FS_READ = 1,
  AEGIS_ACTION_FS_WRITE = 2,
  AEGIS_ACTION_NET_CONNECT = 3,
  AEGIS_ACTION_NET_BIND = 4,
  AEGIS_ACTION_DEVICE_IO = 5
} aegis_action_t;

typedef struct {
  uint8_t allowed;
  char reason[96];
} aegis_policy_decision_t;

typedef struct {
  aegis_sandbox_policy_t policies[128];
  uint8_t active[128];
  size_t count;
} aegis_policy_engine_t;

void aegis_policy_engine_init(aegis_policy_engine_t *engine);
int aegis_policy_engine_set_policy(aegis_policy_engine_t *engine,
                                   const aegis_sandbox_policy_t *policy);
int aegis_policy_engine_remove_policy(aegis_policy_engine_t *engine, uint32_t process_id);
int aegis_policy_engine_check(const aegis_policy_engine_t *engine,
                              const aegis_capability_store_t *store,
                              uint32_t process_id,
                              aegis_action_t action,
                              aegis_policy_decision_t *decision);

#endif

