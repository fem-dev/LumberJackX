#pragma once
#include <opencv2/core.hpp>
namespace lumberjack {
enum class BranchSide { Left, Right, None, Unknown };
class BranchDetector { public: BranchSide detect(const cv::Mat& frame) const; };
}
