cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(adc_offset adc_offset.c)
target_link_libraries(adc_offset ${LIBRARY_NAME})

add_executable(example_1 example_1.c)
target_link_libraries(example_1 ${LIBRARY_NAME})

add_executable(example_2 example_2.c)
target_link_libraries(example_2 ${LIBRARY_NAME})

add_executable(GradientEcho GradientEcho.c bitmap.c)
target_link_libraries(GradientEcho ${LIBRARY_NAME} ${FFT_LIBRARY_NAME})

install(TARGETS adc_offset
		example_1
		example_2
                GradientEcho
        RUNTIME DESTINATION examples/RadioProcessor-G)

