#pragma once

#include <cstdint>

#if defined(_WIN32)
    #if defined(LUMBERJACK_VISION_EXPORTS)
        #define LJX_API __declspec(dllexport)
    #else
        #define LJX_API __declspec(dllimport)
    #endif
    #define LJX_CALL __cdecl
#else
    #define LJX_API
    #define LJX_CALL
#endif

#ifdef __cplusplus
extern "C" {
#endif

enum LJX_BranchSide : int {
    LJX_BRANCH_UNKNOWN = 0,
    LJX_BRANCH_LEFT = 1,
    LJX_BRANCH_RIGHT = 2,
    LJX_BRANCH_NONE = 3
};

// Returns LJX_BRANCH_UNKNOWN until a validated visual classifier is available.
// The buffer is 32-bit BGRA, top-down, with the supplied row stride.
LJX_API int LJX_CALL LJX_DetectBranch(
    const std::uint8_t* bgra,
    int width,
    int height,
    int stride,
    double* confidence
);

#ifdef __cplusplus
}
#endif
