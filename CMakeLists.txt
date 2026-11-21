cmake_minimum_required(VERSION 3.20)
project(LumberJackX VERSION 0.2.0 LANGUAGES CXX)
if(NOT WIN32)
  message(FATAL_ERROR "LumberJackX currently targets Windows 10.")
endif()
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
find_package(OpenCV 4 REQUIRED COMPONENTS core imgproc highgui)
add_executable(LumberJackX
  src/main.cpp src/ScreenCapture.cpp src/Calibration.cpp
  src/BranchDetector.cpp src/DecisionEngine.cpp
  src/GameController.cpp src/Timer.cpp
)
target_include_directories(LumberJackX PRIVATE include ${OpenCV_INCLUDE_DIRS})
target_link_libraries(LumberJackX PRIVATE ${OpenCV_LIBS} user32 gdi32)
target_compile_definitions(LumberJackX PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
if(MSVC)
  target_compile_options(LumberJackX PRIVATE /W4 /permissive- /EHsc)
else()
  target_compile_options(LumberJackX PRIVATE -Wall -Wextra -Wpedantic)
endif()
