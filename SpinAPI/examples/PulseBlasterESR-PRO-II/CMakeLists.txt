cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbesr_pro_ii_example1 pbesr_pro_ii_example1.c)
target_link_libraries(pbesr_pro_ii_example1 ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_example2 pbesr_pro_ii_example2.c)
target_link_libraries(pbesr_pro_ii_example2 ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_example3 pbesr_pro_ii_example3.c)
target_link_libraries(pbesr_pro_ii_example3 ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_example4 pbesr_pro_ii_example4.c)
target_link_libraries(pbesr_pro_ii_example4 ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_example5 pbesr_pro_ii_example5.c)
target_link_libraries(pbesr_pro_ii_example5 ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_reset pbesr_pro_ii_reset.c)
target_link_libraries(pbesr_pro_ii_reset ${LIBRARY_NAME})

add_executable(pbesr_pro_ii_trigger pbesr_pro_ii_trigger.c)
target_link_libraries(pbesr_pro_ii_trigger ${LIBRARY_NAME})

install(TARGETS pbesr_pro_ii_example1
                pbesr_pro_ii_example2
                pbesr_pro_ii_example3
                pbesr_pro_ii_example4
                pbesr_pro_ii_example5
                pbesr_pro_ii_reset
                pbesr_pro_ii_trigger
        RUNTIME DESTINATION examples/PulseBlasterESR-PRO-II)

