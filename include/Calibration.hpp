#pragma once
#include <opencv2/core.hpp>
#include <string>
#include <vector>
namespace lumberjack {
enum class ControlSide { Unassigned, Left, Right };
struct ControlMarker {
    cv::Point point; // Relative to the captured game region.
    ControlSide side{ControlSide::Unassigned};
};
struct AppConfig {
    cv::Rect captureRegion{100, 100, 400, 600};
    std::vector<ControlMarker> controls;
    int sessionSeconds{3600};
    bool load(const std::string& path);
    bool save(const std::string& path) const;
};
}
