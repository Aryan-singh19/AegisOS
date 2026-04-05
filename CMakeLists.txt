cmake_minimum_required(VERSION 3.20)
project(AegisOS C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(kernel_sim STATIC
  kernel/src/kernel_main.c
)
target_include_directories(kernel_sim PUBLIC kernel/include)
target_compile_options(kernel_sim PRIVATE -Wall -Wextra -Wpedantic)

add_executable(kernel_sim_test tests/kernel_sim_test.c)
target_link_libraries(kernel_sim_test PRIVATE kernel_sim)

enable_testing()
add_test(NAME kernel-sim-test COMMAND kernel_sim_test)

