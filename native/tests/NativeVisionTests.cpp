#include "LumberJackVision.h"

#include <cstdint>
#include <vector>

int main() {
    double confidence = 1.0;

    if (LJX_DetectBranch(nullptr, 10, 10, 40, &confidence) != LJX_BRANCH_UNKNOWN) {
        return 1;
    }
    if (confidence != 0.0) {
        return 2;
    }

    std::vector<std::uint8_t> pixels(4U * 20U * 30U, 0U);
    confidence = 1.0;
    if (LJX_DetectBranch(pixels.data(), 20, 30, 80, &confidence) != LJX_BRANCH_UNKNOWN) {
        return 3;
    }
    if (confidence != 0.0) {
        return 4;
    }

    if (LJX_DetectBranch(pixels.data(), 20, 30, 10, &confidence) != LJX_BRANCH_UNKNOWN) {
        return 5;
    }

    return 0;
}
