#include <stdio.h>
#include <string.h>

#include "sandbox_policy.h"

static int test_valid_policy(void) {
  aegis_sandbox_policy_t policy = {
      10u, AEGIS_CAP_FS_READ | AEGIS_CAP_NET_CLIENT, 1u, 0u, 1u, 0u, 0u};
  char reason[64];

  if (!aegis_sandbox_policy_validate(&policy, reason, sizeof(reason))) {
    fprintf(stderr, "expected valid policy, got: %s\n", reason);
    return 1;
  }
  if (!aegis_sandbox_policy_allows(&policy, AEGIS_CAP_FS_READ)) {
    fprintf(stderr, "expected FS_READ to be allowed\n");
    return 1;
  }
  if (aegis_sandbox_policy_allows(&policy, AEGIS_CAP_FS_WRITE)) {
    fprintf(stderr, "expected FS_WRITE to be denied\n");
    return 1;
  }
  return 0;
}

static int test_invalid_policy(void) {
  aegis_sandbox_policy_t bad_policy = {0u, AEGIS_CAP_NET_SERVER, 0u, 0u, 0u, 1u, 0u};
  char reason[64];

  if (aegis_sandbox_policy_validate(&bad_policy, reason, sizeof(reason))) {
    fprintf(stderr, "expected invalid policy to fail\n");
    return 1;
  }
  if (strcmp(reason, "process_id must be non-zero") != 0) {
    fprintf(stderr, "unexpected reason: %s\n", reason);
    return 1;
  }
  return 0;
}

int main(void) {
  if (test_valid_policy() != 0) {
    return 1;
  }
  if (test_invalid_policy() != 0) {
    return 1;
  }
  puts("sandbox policy tests passed");
  return 0;
}

