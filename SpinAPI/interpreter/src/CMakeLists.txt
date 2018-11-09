cmake_minimum_required(VERSION 3.6)

project(interpreter)

if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX ".")
endif() 

if(NOT DEFINED LIBRARY_NAME)
  if(${ARCHITECTURE} STREQUAL "x64") 
    set(LIBRARY_NAME "spinapi64" CACHE STRING "API Name")
  else()
    set(LIBRARY_NAME "spinapi" CACHE STRING "API Name")
  endif()
endif()

set(INTERPRETER_CMD_SRC commandline.cpp interpreter.cpp)
set(INTERPRETER_GUI_SRC gui.cpp interpreter.cpp)
include_directories(.)

add_executable(spbicl ${INTERPRETER_CMD_SRC})
target_link_libraries(spbicl ${LIBRARY_NAME})
install(TARGETS spbicl RUNTIME DESTINATION interpreter/)

if(WIN32)
  add_executable(spbi WIN32 ${INTERPRETER_GUI_SRC} rc/resources.rc)
  target_link_libraries(spbi ${LIBRARY_NAME})
  install(TARGETS spbi RUNTIME DESTINATION interpreter/)
endif()

