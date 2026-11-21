#include "LumberJackVision.h"

#include <limits>

int LJX_CALL LJX_DetectBranch(
    const std::uint8_t* bgra,
    const int width,
    const int height,
    const int stride,
    double* confidence) {

    if (confidence != nullptr) {
        *confidence = 0.0;
    }

    // Keep detection fail-closed. A future classifier must be validated against
    // representative game frames before it is allowed to return Left or Right.
    if (bgra == nullptr || width <= 0 || height <= 0) {
        return LJX_BRANCH_UNKNOWN;
    }

    if (width > (std::numeric_limits<int>::max() / 4) || stride < width * 4) {
        return LJX_BRANCH_UNKNOWN;
    }

    return LJX_BRANCH_UNKNOWN;
}
