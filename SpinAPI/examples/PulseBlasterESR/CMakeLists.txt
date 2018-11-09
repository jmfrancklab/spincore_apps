cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbesr_long_delay_test pbesr_long_delay_test.c)
target_link_libraries(pbesr_long_delay_test ${LIBRARY_NAME})

add_executable(pbesr_loop_test pbesr_loop_test.c)
target_link_libraries(pbesr_loop_test ${LIBRARY_NAME})

add_executable(pbesr_manual_example pbesr_manual_example.c)
target_link_libraries(pbesr_manual_example ${LIBRARY_NAME})

add_executable(pbesr_sub_test pbesr_sub_test.c)
target_link_libraries(pbesr_sub_test ${LIBRARY_NAME})

install(TARGETS pbesr_long_delay_test
                pbesr_loop_test
                pbesr_manual_example
                pbesr_sub_test
        RUNTIME DESTINATION examples/PulseBlasterESR)

