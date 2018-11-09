cmake_minimum_required(VERSION 3.6)

if(WIN32)
  add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

add_executable(pts_fsweep pts_fsweep.c)
target_link_libraries(pts_fsweep ${LIBRARY_NAME})

add_executable(usb-pts_ex_160 usb-pts_ex_160.c)
target_link_libraries(usb_pts_ex-160 ${LIBRARY_NAME})

add_executable(usb-pts_ex_250 usb-pts_ex_250.c)
target_link_libraries(usb_pts_ex-250 ${LIBRARY_NAME})

add_executable(usb-pts_ex_300 usb-pts_ex_300.c)
target_link_libraries(usb_pts_ex-300 ${LIBRARY_NAME})

add_executable(usb-pts_ex_500 usb-pts_ex_500.c)
target_link_libraries(usb_pts_ex-500 ${LIBRARY_NAME})

add_executable(usb-pts_ex_3200 usb-pts_ex_3200.c)
target_link_libraries(usb_pts_ex-3200 ${LIBRARY_NAME})

install(TARGETS usb-pts_ex_160
                usb-pts_ex_250
                usb-pts_ex_300
                usb-pts_ex_500
                usb-pts_ex_3200
        RUNTIME DESTINATION examples/PBDDS-III)

