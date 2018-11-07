cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(awg awg.c)
target_link_libraries(awg ${LIBRARY_NAME})

add_executable(CYCLOPS_nmr CYCLOPS_nmr.c)
target_link_libraries(CYCLOPS_nmr ${LIBRARY_NAME})

add_executable(DirectCapture DirectCapture.c)
target_link_libraries(DirectCapture ${LIBRARY_NAME})

add_executable(excite_test excite_test.c)
target_link_libraries(excite_test ${LIBRARY_NAME})

add_executable(singlepulse_nmr singlepulse_nmr.c)
target_link_libraries(singlepulse_nmr ${LIBRARY_NAME})

#add_executable(singlepulse_nmr_shift singlepulse_nmr_shift.c)
#target_link_libraries(singlepulse_nmr_shift ${LIBRARY_NAME})

install(TARGETS awg
                CYCLOPS_nmr
                DirectCapture
                excite_test
                singlepulse_nmr
        RUNTIME DESTINATION examples/RadioProcessor)

