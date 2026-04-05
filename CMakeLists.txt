cmake_minimum_required(VERSION 3.20)
project(AegisOS C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(kernel_sim STATIC
  kernel/src/kernel_main.c
)
target_include_directories(kernel_sim PUBLIC kernel/include)
target_compile_options(kernel_sim PRIVATE -Wall -Wextra -Wpedantic)

add_library(aegis_capability STATIC
  userland/security/capability.c
)
target_include_directories(aegis_capability PUBLIC userland/include)
target_compile_options(aegis_capability PRIVATE -Wall -Wextra -Wpedantic)

add_library(aegis_sandbox STATIC
  userland/security/sandbox_policy.c
)
target_include_directories(aegis_sandbox PUBLIC userland/include)
target_compile_options(aegis_sandbox PRIVATE -Wall -Wextra -Wpedantic)

add_executable(kernel_sim_test tests/kernel_sim_test.c)
target_link_libraries(kernel_sim_test PRIVATE kernel_sim)

add_executable(capability_test tests/capability_test.c)
target_link_libraries(capability_test PRIVATE aegis_capability)

add_executable(sandbox_policy_test tests/sandbox_policy_test.c)
target_link_libraries(sandbox_policy_test PRIVATE aegis_sandbox)

enable_testing()
add_test(NAME kernel-sim-test COMMAND kernel_sim_test)
add_test(NAME capability-test COMMAND capability_test)
add_test(NAME sandbox-policy-test COMMAND sandbox_policy_test)
