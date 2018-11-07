cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbdds3_ex1 pbdds3_ex1.c)
target_link_libraries(pbdds3_ex1 ${LIBRARY_NAME})

add_executable(pbdds3_ex2 pbdds3_ex2.c)
target_link_libraries(pbdds3_ex2 ${LIBRARY_NAME})

install(TARGETS pbdds3_ex1 pbdds3_ex2
        RUNTIME DESTINATION examples/PBDDS-III)

