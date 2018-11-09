cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pbdds_i_300_amplitude_sweep pbdds_i_300_amplitude_sweep.c)
target_link_libraries(pbdds_i_300_amplitude_sweep ${LIBRARY_NAME})

add_executable(pbdds_i_300_awg pbdds_i_300_awg.c)
target_link_libraries(pbdds_i_300_awg ${LIBRARY_NAME})

add_executable(pbdds_i_300_awg_ramp pbdds_i_300_awg_ramp.c)
target_link_libraries(pbdds_i_300_awg_ramp ${LIBRARY_NAME})

add_executable(pbdds_i_300_bipolar_square_wave pbdds_i_300_bipolar_square_wave.c)
target_link_libraries(pbdds_i_300_bipolar_square_wave ${LIBRARY_NAME})

add_executable(pbdds_i_300_cont pbdds_i_300_cont.c)
target_link_libraries(pbdds_i_300_cont ${LIBRARY_NAME})

add_executable(pbdds_i_300_excite_test pbdds_i_300_excite_test.c)
target_link_libraries(pbdds_i_300_excite_test ${LIBRARY_NAME})

add_executable(pbdds_i_300_frequency_sweep pbdds_i_300_frequency_sweep.c)
target_link_libraries(pbdds_i_300_frequency_sweep ${LIBRARY_NAME})

add_executable(pbdds_i_300_phase_test pbdds_i_300_phase_test.c)
target_link_libraries(pbdds_i_300_phase_test ${LIBRARY_NAME})

install(TARGETS pbdds_i_300_amplitude_sweep 
                pbdds_i_300_awg
                pbdds_i_300_awg_ramp
                pbdds_i_300_bipolar_square_wave
                pbdds_i_300_cont
                pbdds_i_300_excite_test
                pbdds_i_300_frequency_sweep
                pbdds_i_300_phase_test
        RUNTIME DESTINATION examples/PulseBlasterDDS-I)

