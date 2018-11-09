cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbdds2_awg pbdds2_awg.c)
target_link_libraries(pbdds2_awg ${LIBRARY_NAME})

add_executable(pbdds2_excite_test pbdds2_excite_test.c)
target_link_libraries(pbdds2_excite_test ${LIBRARY_NAME})

add_executable(pbdds2_load_shape_ram pbdds2_load_shape_ram.c)
target_link_libraries(pbdds2_load_shape_ram ${LIBRARY_NAME})

add_executable(pbdds2_startAddress_default pbdds2_startAddress_default.c)
target_link_libraries(pbdds2_startAddress_default ${LIBRARY_NAME})

add_executable(pbdds2_TTL_only pbdds2_TTL_only.c)
target_link_libraries(pbdds2_TTL_only ${LIBRARY_NAME})

add_executable(pbdds2_TTLflag_default pbdds2_TTLflag_default.c)
target_link_libraries(pbdds2_TTLflag_default ${LIBRARY_NAME})

install(TARGETS pbdds2_awg
                pbdds2_excite_test
                pbdds2_load_shape_ram
                pbdds2_startAddress_default
                pbdds2_TTL_only
                pbdds2_TTLflag_default
        RUNTIME DESTINATION examples/PulseBlasterDDS-II)

