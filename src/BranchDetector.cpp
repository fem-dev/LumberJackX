#include "BranchDetector.hpp"
namespace lumberjack {
BranchSide BranchDetector::detect(const cv::Mat& frame) const {
  if (frame.empty()) return BranchSide::Unknown;
  // Safe placeholder: calibrate ROI/features from actual game screenshots before enabling moves.
  return BranchSide::Unknown;
}
}
