############################
# INCLUDE
# - tell cmake where the .h files are

include_directories(common)



############################
# COMPILER SETTINGS
# - the important one is std=gnu99, which allows declaration of variables
#   in for loops, in c source files

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")
#set(CMAKE_CXX_FLAGS "${CMAKE_C_FLAGS} -std=gnu99")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})


############################
# DEPENDENCIES

find_package(OpenCV REQUIRED)
find_package(Boost REQUIRED COMPONENTS system filesystem)



############################
# BUILD LIBRARY

add_library(apriltags SHARED apriltag.c apriltag_quad_thresh.c tag16h5.c tag25h7.c tag25h9.c tag36h10.c tag36h11.c tag36artoolkit.c common/g2d.c common/zarray.c common/zhash.c common/zmaxheap.c common/unionfind.c common/matd.c common/image_u8.c common/image_u8x3.c common/image_u8x4.c common/pam.c common/pnm.c common/image_f32.c common/workerpool.c common/time_util.c common/svd22.c common/homography.c common/string_util.c common/getopt.c common/pjpeg.c common/pjpeg-idct.c)
target_link_libraries(apriltags pthread m ${OpenCV_LIBS})
target_include_directories(apriltags PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})


############################
# BUILD EXECUTABLE

# demos
add_executable(apriltag_demo app/apriltag_demo.c)
target_link_libraries(apriltag_demo pthread m apriltags)
add_executable(opencv_demo app/opencv_demo.cc)
target_link_libraries(opencv_demo pthread m apriltags ${OpenCV_LIBS})

# custom apriltag executable
add_executable(detect_apriltag app/detect_apriltags.cc)
target_link_libraries(detect_apriltag pthread m apriltags ${OpenCV_LIBS} ${Boost_LIBRARIES})
set_target_properties(detect_apriltag PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${opensfm_SOURCE_DIR}/../commands")