#include "sandbox_engine.h"

#include <stdio.h>
#include <string.h>

static void set_reason(aegis_policy_decision_t *decision, const char *message, uint8_t allowed) {
  if (decision == 0) {
    return;
  }
  decision->allowed = allowed;
  if (message == 0) {
    decision->reason[0] = '\0';
    return;
  }
  snprintf(decision->reason, sizeof(decision->reason), "%s", message);
}

static int find_policy_index(const aegis_policy_engine_t *engine, uint32_t process_id, size_t *index) {
  size_t i;
  if (engine == 0 || index == 0 || process_id == 0) {
    return 0;
  }
  for (i = 0; i < engine->count; ++i) {
    if (engine->active[i] != 0 && engine->policies[i].process_id == process_id) {
      *index = i;
      return 1;
    }
  }
  return 0;
}

static uint32_t action_to_capability(aegis_action_t action, const aegis_sandbox_policy_t *policy,
                                     uint8_t *policy_gate) {
  if (policy_gate != 0) {
    *policy_gate = 0;
  }
  switch (action) {
    case AEGIS_ACTION_FS_READ:
      if (policy_gate != 0) {
        *policy_gate = policy->allow_fs_read;
      }
      return AEGIS_CAP_FS_READ;
    case AEGIS_ACTION_FS_WRITE:
      if (policy_gate != 0) {
        *policy_gate = policy->allow_fs_write;
      }
      return AEGIS_CAP_FS_WRITE;
    case AEGIS_ACTION_NET_CONNECT:
      if (policy_gate != 0) {
        *policy_gate = policy->allow_net_client;
      }
      return AEGIS_CAP_NET_CLIENT;
    case AEGIS_ACTION_NET_BIND:
      if (policy_gate != 0) {
        *policy_gate = policy->allow_net_server;
      }
      return AEGIS_CAP_NET_SERVER;
    case AEGIS_ACTION_DEVICE_IO:
      if (policy_gate != 0) {
        *policy_gate = policy->allow_device_io;
      }
      return AEGIS_CAP_DEVICE_IO;
    default:
      return AEGIS_CAP_NONE;
  }
}

void aegis_policy_engine_init(aegis_policy_engine_t *engine) {
  size_t i;
  if (engine == 0) {
    return;
  }
  engine->count = 0;
  for (i = 0; i < 128; ++i) {
    engine->active[i] = 0;
  }
}

int aegis_policy_engine_set_policy(aegis_policy_engine_t *engine,
                                   const aegis_sandbox_policy_t *policy) {
  size_t index = 0;
  char reason[96];
  if (engine == 0 || policy == 0) {
    return -1;
  }
  if (!aegis_sandbox_policy_validate(policy, reason, sizeof(reason))) {
    return -1;
  }
  if (find_policy_index(engine, policy->process_id, &index)) {
    engine->policies[index] = *policy;
    return 0;
  }
  if (engine->count >= 128) {
    return -1;
  }
  engine->policies[engine->count] = *policy;
  engine->active[engine->count] = 1;
  engine->count += 1;
  return 0;
}

int aegis_policy_engine_remove_policy(aegis_policy_engine_t *engine, uint32_t process_id) {
  size_t index = 0;
  if (!find_policy_index(engine, process_id, &index)) {
    return -1;
  }
  engine->active[index] = 0;
  return 0;
}

int aegis_policy_engine_check(const aegis_policy_engine_t *engine,
                              const aegis_capability_store_t *store,
                              uint32_t process_id,
                              aegis_action_t action,
                              aegis_policy_decision_t *decision) {
  size_t index = 0;
  uint8_t gate = 0;
  uint32_t cap_bit;
  if (decision != 0) {
    decision->allowed = 0;
    decision->reason[0] = '\0';
  }
  if (engine == 0 || store == 0 || process_id == 0 || decision == 0) {
    set_reason(decision, "invalid input", 0);
    return -1;
  }
  if (!find_policy_index(engine, process_id, &index)) {
    set_reason(decision, "no sandbox policy for process", 0);
    return 0;
  }
  cap_bit = action_to_capability(action, &engine->policies[index], &gate);
  if (cap_bit == AEGIS_CAP_NONE) {
    set_reason(decision, "unknown action", 0);
    return 0;
  }
  if (gate == 0) {
    set_reason(decision, "blocked by sandbox policy gate", 0);
    return 0;
  }
  if (!aegis_capability_is_allowed(store, process_id, cap_bit)) {
    set_reason(decision, "missing capability token permission", 0);
    return 0;
  }
  set_reason(decision, "allowed", 1);
  return 1;
}

