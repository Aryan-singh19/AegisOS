#include "capability.h"

static int capability_find_index(const aegis_capability_store_t *store, uint32_t process_id,
                                 size_t *index) {
  size_t i;
  if (store == 0 || index == 0 || process_id == 0) {
    return 0;
  }
  for (i = 0; i < store->count; ++i) {
    if (store->active[i] != 0 && store->tokens[i].process_id == process_id) {
      *index = i;
      return 1;
    }
  }
  return 0;
}

int aegis_capability_validate(const aegis_capability_token_t *token,
                              uint32_t requested_permissions) {
  if (token == 0) {
    return 0;
  }
  if (token->process_id == 0) {
    return 0;
  }
  return (token->permissions & requested_permissions) == requested_permissions;
}

static int capability_expired(const aegis_capability_token_t *token, uint64_t now_epoch) {
  if (token == 0) {
    return 1;
  }
  if (token->expires_at_epoch == 0) {
    return 0;
  }
  return now_epoch >= token->expires_at_epoch;
}

void aegis_capability_store_init(aegis_capability_store_t *store) {
  size_t i;
  if (store == 0) {
    return;
  }
  store->count = 0;
  for (i = 0; i < 128; ++i) {
    store->active[i] = 0;
    store->tokens[i].process_id = 0;
    store->tokens[i].permissions = AEGIS_CAP_NONE;
    store->tokens[i].issued_at_epoch = 0;
    store->tokens[i].expires_at_epoch = 0;
    store->tokens[i].rotation_counter = 0;
  }
}

int aegis_capability_issue(aegis_capability_store_t *store, uint32_t process_id,
                           uint32_t permissions) {
  return aegis_capability_issue_with_ttl(store, process_id, permissions, 0, 0);
}

int aegis_capability_issue_with_ttl(aegis_capability_store_t *store, uint32_t process_id,
                                    uint32_t permissions, uint64_t now_epoch,
                                    uint64_t ttl_seconds) {
  size_t existing = 0;
  if (store == 0 || process_id == 0) {
    return -1;
  }
  if (capability_find_index(store, process_id, &existing)) {
    store->tokens[existing].permissions = permissions;
    store->tokens[existing].issued_at_epoch = now_epoch;
    store->tokens[existing].expires_at_epoch = ttl_seconds == 0 ? 0 : now_epoch + ttl_seconds;
    return 0;
  }
  if (store->count >= 128) {
    return -1;
  }
  store->tokens[store->count].process_id = process_id;
  store->tokens[store->count].permissions = permissions;
  store->tokens[store->count].issued_at_epoch = now_epoch;
  store->tokens[store->count].expires_at_epoch = ttl_seconds == 0 ? 0 : now_epoch + ttl_seconds;
  store->tokens[store->count].rotation_counter = 0;
  store->active[store->count] = 1;
  store->count += 1;
  return 0;
}

int aegis_capability_rotate(aegis_capability_store_t *store, uint32_t process_id,
                            uint32_t permissions, uint64_t now_epoch, uint64_t ttl_seconds) {
  size_t index = 0;
  if (store == 0 || process_id == 0) {
    return -1;
  }
  if (!capability_find_index(store, process_id, &index)) {
    return -1;
  }
  store->tokens[index].permissions = permissions;
  store->tokens[index].issued_at_epoch = now_epoch;
  store->tokens[index].expires_at_epoch = ttl_seconds == 0 ? 0 : now_epoch + ttl_seconds;
  store->tokens[index].rotation_counter += 1;
  return 0;
}

int aegis_capability_revoke(aegis_capability_store_t *store, uint32_t process_id) {
  size_t index = 0;
  if (!capability_find_index(store, process_id, &index)) {
    return -1;
  }
  store->active[index] = 0;
  store->tokens[index].permissions = AEGIS_CAP_NONE;
  store->tokens[index].issued_at_epoch = 0;
  store->tokens[index].expires_at_epoch = 0;
  store->tokens[index].rotation_counter = 0;
  return 0;
}

int aegis_capability_is_allowed(const aegis_capability_store_t *store, uint32_t process_id,
                                uint32_t requested_permissions) {
  return aegis_capability_is_allowed_at(store, process_id, requested_permissions, 0);
}

int aegis_capability_is_allowed_at(const aegis_capability_store_t *store, uint32_t process_id,
                                   uint32_t requested_permissions, uint64_t now_epoch) {
  size_t index = 0;
  if (!capability_find_index(store, process_id, &index)) {
    return 0;
  }
  if (now_epoch != 0 && capability_expired(&store->tokens[index], now_epoch)) {
    return 0;
  }
  return aegis_capability_validate(&store->tokens[index], requested_permissions);
}
