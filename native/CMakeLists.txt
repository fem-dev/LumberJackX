add_library(LumberJackVision SHARED
    src/LumberJackVision.cpp
)

target_include_directories(LumberJackVision
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_definitions(LumberJackVision PRIVATE
    LUMBERJACK_VISION_EXPORTS
    WIN32_LEAN_AND_MEAN
    NOMINMAX
)

if(MSVC)
    target_compile_options(LumberJackVision PRIVATE /W4 /permissive- /EHsc)
    set_property(TARGET LumberJackVision PROPERTY
        MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
    )
else()
    target_compile_options(LumberJackVision PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(BUILD_TESTING)
    add_executable(NativeVisionTests
        tests/NativeVisionTests.cpp
    )
    target_link_libraries(NativeVisionTests PRIVATE LumberJackVision)
    add_test(NAME LumberJackX.NativeVision COMMAND NativeVisionTests)
endif()
