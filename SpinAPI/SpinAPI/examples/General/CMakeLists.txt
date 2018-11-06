cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pb_start pb_start.c)
target_link_libraries(pb_start ${LIBRARY_NAME})

add_executable(pb_stop pb_stop.c)
target_link_libraries(pb_stop ${LIBRARY_NAME})

add_executable(pb_debug pb_debug.c)
target_link_libraries(pb_debug ${LIBRARY_NAME})

add_executable(pb_read_firmware pb_read_firmware.c)
target_link_libraries(pb_read_firmware ${LIBRARY_NAME})

install(TARGETS pb_start pb_stop pb_debug pb_read_firmware
        RUNTIME DESTINATION examples/General/)

