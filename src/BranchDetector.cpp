#include "BranchDetector.hpp"
namespace lumberjack {
Detection BranchDetector::detect(const cv::Mat& frame) const {
  // Fail closed until the visual classifier is calibrated against genuine
  // gameplay frames. Guessing a side can cause repeated incorrect input.
  if (frame.empty()) return {};
  return {BranchSide::Unknown, 0.0};
}
}
