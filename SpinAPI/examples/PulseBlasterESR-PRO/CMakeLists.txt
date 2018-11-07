cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbesr_pro_example1 pbesr_pro_example1.c)
target_link_libraries(pbesr_pro_example1 ${LIBRARY_NAME})

add_executable(pbesr_pro_long_delay_test pbesr_pro_long_delay_test.c)
target_link_libraries(pbesr_pro_long_delay_test ${LIBRARY_NAME})

add_executable(pbesr_pro_loop_test pbesr_pro_loop_test.c)
target_link_libraries(pbesr_pro_loop_test ${LIBRARY_NAME})

add_executable(pbesr_pro_shortpulse_disable pbesr_pro_shortpulse_disable.c)
target_link_libraries(pbesr_pro_shortpulse_disable ${LIBRARY_NAME})

add_executable(pbesr_pro_start_address pbesr_pro_start_address.c)
target_link_libraries(pbesr_pro_start_address ${LIBRARY_NAME})

add_executable(pbesr_pro_subtest pbesr_pro_subtest.c)
target_link_libraries(pbesr_pro_subtest ${LIBRARY_NAME})

install(TARGETS pbesr_pro_example1
                pbesr_pro_long_delay_test
                pbesr_pro_loop_test
                pbesr_pro_shortpulse_disable
                pbesr_pro_start_address
                pbesr_pro_subtest
        RUNTIME DESTINATION examples/PulseBlasterESR-PRO)

