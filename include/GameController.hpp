#pragma once
#include <opencv2/core.hpp>
namespace lumberjack {
class GameController {
public:
  bool clickAt(const cv::Point& desktopPoint) const;
};
}
