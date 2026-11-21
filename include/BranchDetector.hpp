#pragma once
#include <opencv2/core.hpp>
namespace lumberjack {
enum class BranchSide { Left, Right, None, Unknown };
struct Detection { BranchSide side{BranchSide::Unknown}; double confidence{0.0}; };
class BranchDetector { public: Detection detect(const cv::Mat& frame) const; };
}
