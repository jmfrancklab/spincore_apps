cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pb24_ex1 pb24_ex1.c)
target_link_libraries(pb24_ex1 ${LIBRARY_NAME})

add_executable(pb24_ex2 pb24_ex2.c)
target_link_libraries(pb24_ex2 ${LIBRARY_NAME})

add_executable(pb24_ex3 pb24_ex3.c)
target_link_libraries(pb24_ex3 ${LIBRARY_NAME})

add_executable(pb24_ex4 pb24_ex4.c)
target_link_libraries(pb24_ex4 ${LIBRARY_NAME})

add_executable(pb24_mem_depth_test pb24_mem_depth_test.c)
target_link_libraries(pb24_mem_depth_test ${LIBRARY_NAME})

add_executable(pb24_programmable_clock pb24_programmable_clock.c)
target_link_libraries(pb24_programmable_clock ${LIBRARY_NAME})

add_executable(pb24_two_boards pb24_two_boards.c)
target_link_libraries(pb24_two_boards ${LIBRARY_NAME})

install(TARGETS pb24_ex1 pb24_ex2 pb24_ex3 pb24_ex4 pb24_mem_depth_test pb24_programmable_clock pb24_two_boards
        RUNTIME DESTINATION examples/PulseBlaster24)

