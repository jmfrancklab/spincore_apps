cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(incl_160 incl160.c)
target_link_libraries(incl_160 ${LIBRARY_NAME})

add_executable(incl_250 incl250.c)
target_link_libraries(incl_250 ${LIBRARY_NAME})

add_executable(incl_300 incl300.c)
target_link_libraries(incl_300 ${LIBRARY_NAME})

add_executable(incl_500 incl500.c)
target_link_libraries(incl_500 ${LIBRARY_NAME})

add_executable(incl_3200 incl3200.c)
target_link_libraries(incl_3200 ${LIBRARY_NAME})

add_executable(incl_fsweep_once_160 incl_fsweep_once_160.c)
target_link_libraries(incl_fsweep_once_160 ${LIBRARY_NAME})

add_executable(incl_fsweep_once_250 incl_fsweep_once_250.c)
target_link_libraries(incl_fsweep_once_250 ${LIBRARY_NAME})

add_executable(incl_fsweep_once_300 incl_fsweep_once_300.c)
target_link_libraries(incl_fsweep_once_300 ${LIBRARY_NAME})

add_executable(incl_fsweep_once_500 incl_fsweep_once_500.c)
target_link_libraries(incl_fsweep_once_500 ${LIBRARY_NAME})

add_executable(incl_fsweep_once_3200 incl_fsweep_once_3200.c)
target_link_libraries(incl_fsweep_once_3200 ${LIBRARY_NAME})

install(TARGETS incl_fsweep_once_160
                incl_fsweep_once_250
                incl_fsweep_once_300
                incl_fsweep_once_500
                incl_fsweep_once_3200
                incl_160
                incl_250
                incl_300
                incl_500
                incl_3200
        RUNTIME DESTINATION examples/USB-PTS/includes)

