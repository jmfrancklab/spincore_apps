cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pb_quadcore250_example1 pb_quadcore250_example1.c)
target_link_libraries(pb_quadcore250_example1 ${LIBRARY_NAME})

add_executable(pb_quadcore250_example2 pb_quadcore250_example2.c)
target_link_libraries(pb_quadcore250_example2 ${LIBRARY_NAME})

add_executable(pb_quadcore250_example3 pb_quadcore250_example3.c)
target_link_libraries(pb_quadcore250_example3 ${LIBRARY_NAME})

add_executable(pb_quadcore250_example4 pb_quadcore250_example4.c)
target_link_libraries(pb_quadcore250_example4 ${LIBRARY_NAME})

add_executable(pb_quadcore500_example1 pb_quadcore500_example1.c)
target_link_libraries(pb_quadcore500_example1 ${LIBRARY_NAME})

add_executable(pb_quadcore500_example2 pb_quadcore500_example2.c)
target_link_libraries(pb_quadcore500_example2 ${LIBRARY_NAME})

add_executable(pb_quadcore500_example3 pb_quadcore500_example3.c)
target_link_libraries(pb_quadcore500_example3 ${LIBRARY_NAME})

install(TARGETS pb_quadcore250_example1
                pb_quadcore250_example2
                pb_quadcore250_example3
                pb_quadcore250_example4
                pb_quadcore500_example1
                pb_quadcore500_example2
                pb_quadcore500_example3
        RUNTIME DESTINATION examples/PulseBlaster-QuadCore)

