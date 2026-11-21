#include "Calibration.hpp"
#include <opencv2/core/persistence.hpp>
#include <algorithm>
#include <filesystem>

namespace lumberjack {
bool AppConfig::load(const std::string& path) {
    try {
        cv::FileStorage fs(path, cv::FileStorage::READ);
        if (!fs.isOpened()) return false;
        int x=captureRegion.x, y=captureRegion.y, w=captureRegion.width, h=captureRegion.height;
        fs["capture_x"] >> x; fs["capture_y"] >> y;
        fs["capture_width"] >> w; fs["capture_height"] >> h;
        fs["session_seconds"] >> sessionSeconds;
        if (w <= 0 || h <= 0) return false;
        captureRegion = {x,y,w,h};
        controls.clear();
        const cv::FileNode nodes = fs["controls"];
        for (const auto& node : nodes) {
            int px=0, py=0;
            std::string side;
            node["x"] >> px; node["y"] >> py; node["side"] >> side;
            controls.push_back({{px,py}, side == "right" ? ControlSide::Right : ControlSide::Left});
        }
        sessionSeconds = std::clamp(sessionSeconds, 1, 24*60*60);
        return true;
    } catch (const cv::Exception&) {
        return false;
    }
}

bool AppConfig::save(const std::string& path) const {
    try {
        cv::FileStorage fs(path, cv::FileStorage::WRITE);
        if (!fs.isOpened()) return false;
        fs << "capture_x" << captureRegion.x << "capture_y" << captureRegion.y
           << "capture_width" << captureRegion.width << "capture_height" << captureRegion.height
           << "session_seconds" << sessionSeconds;
        fs << "controls" << "[";
        for (const auto& marker : controls) {
            fs << "{" << "x" << marker.point.x << "y" << marker.point.y
               << "side" << (marker.side == ControlSide::Left ? "left" : "right") << "}";
        }
        fs << "]";
        return true;
    } catch (const cv::Exception&) {
        return false;
    }
}
}
