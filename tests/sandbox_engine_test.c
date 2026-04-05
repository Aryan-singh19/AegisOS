#include <stdio.h>
#include <string.h>

#include "capability.h"
#include "sandbox_engine.h"
#include "sandbox_policy.h"

static int test_allow_path(void) {
  aegis_capability_store_t cap_store;
  aegis_policy_engine_t engine;
  aegis_sandbox_policy_t policy = {
      2001u, AEGIS_CAP_FS_READ | AEGIS_CAP_NET_CLIENT, 1u, 0u, 1u, 0u, 0u};
  aegis_policy_decision_t decision;

  aegis_capability_store_init(&cap_store);
  aegis_policy_engine_init(&engine);

  if (aegis_capability_issue(&cap_store, 2001u, AEGIS_CAP_FS_READ | AEGIS_CAP_NET_CLIENT) != 0) {
    fprintf(stderr, "capability issue failed\n");
    return 1;
  }
  if (aegis_policy_engine_set_policy(&engine, &policy) != 0) {
    fprintf(stderr, "set policy failed\n");
    return 1;
  }
  if (aegis_policy_engine_check(&engine, &cap_store, 2001u, AEGIS_ACTION_FS_READ, &decision) != 1) {
    fprintf(stderr, "expected FS_READ allow, got: %s\n", decision.reason);
    return 1;
  }
  if (decision.allowed == 0) {
    fprintf(stderr, "decision.allowed should be true\n");
    return 1;
  }
  return 0;
}

static int test_deny_missing_capability(void) {
  aegis_capability_store_t cap_store;
  aegis_policy_engine_t engine;
  aegis_sandbox_policy_t policy = {
      2002u, AEGIS_CAP_FS_READ | AEGIS_CAP_FS_WRITE, 1u, 1u, 0u, 0u, 0u};
  aegis_policy_decision_t decision;

  aegis_capability_store_init(&cap_store);
  aegis_policy_engine_init(&engine);

  if (aegis_capability_issue(&cap_store, 2002u, AEGIS_CAP_FS_READ) != 0) {
    fprintf(stderr, "capability issue failed\n");
    return 1;
  }
  if (aegis_policy_engine_set_policy(&engine, &policy) != 0) {
    fprintf(stderr, "set policy failed\n");
    return 1;
  }
  if (aegis_policy_engine_check(&engine, &cap_store, 2002u, AEGIS_ACTION_FS_WRITE, &decision) != 0) {
    fprintf(stderr, "expected FS_WRITE deny path\n");
    return 1;
  }
  if (strcmp(decision.reason, "missing capability token permission") != 0) {
    fprintf(stderr, "unexpected reason: %s\n", decision.reason);
    return 1;
  }
  return 0;
}

static int test_deny_policy_gate(void) {
  aegis_capability_store_t cap_store;
  aegis_policy_engine_t engine;
  aegis_sandbox_policy_t policy = {
      2003u, AEGIS_CAP_DEVICE_IO, 0u, 0u, 0u, 0u, 0u};
  aegis_policy_decision_t decision;

  aegis_capability_store_init(&cap_store);
  aegis_policy_engine_init(&engine);

  if (aegis_capability_issue(&cap_store, 2003u, AEGIS_CAP_DEVICE_IO) != 0) {
    fprintf(stderr, "capability issue failed\n");
    return 1;
  }
  if (aegis_policy_engine_set_policy(&engine, &policy) != 0) {
    fprintf(stderr, "set policy failed\n");
    return 1;
  }
  if (aegis_policy_engine_check(&engine, &cap_store, 2003u, AEGIS_ACTION_DEVICE_IO, &decision) != 0) {
    fprintf(stderr, "expected DEVICE_IO deny path\n");
    return 1;
  }
  if (strcmp(decision.reason, "blocked by sandbox policy gate") != 0) {
    fprintf(stderr, "unexpected reason: %s\n", decision.reason);
    return 1;
  }
  return 0;
}

int main(void) {
  if (test_allow_path() != 0) {
    return 1;
  }
  if (test_deny_missing_capability() != 0) {
    return 1;
  }
  if (test_deny_policy_gate() != 0) {
    return 1;
  }
  puts("sandbox engine tests passed");
  return 0;
}

