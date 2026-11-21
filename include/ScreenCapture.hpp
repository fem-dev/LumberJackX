#pragma once
#include <opencv2/core.hpp>
#include <windows.h>
namespace lumberjack {
struct CaptureRegion { int x{0}; int y{0}; int width{400}; int height{600}; };
class ScreenCapture { public: cv::Mat capture(const CaptureRegion& region) const; };
}
