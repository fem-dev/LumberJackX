#include "Calibration.hpp"
#include <opencv2/core/persistence.hpp>
#include <algorithm>
namespace lumberjack {
bool AppConfig::load(const std::string& path) {
    try {
        cv::FileStorage fs(path, cv::FileStorage::READ);
        if (!fs.isOpened()) return false;
        int x=captureRegion.x, y=captureRegion.y, w=captureRegion.width, h=captureRegion.height;
        fs["capture_x"] >> x; fs["capture_y"] >> y;
        fs["capture_width"] >> w; fs["capture_height"] >> h;
        fs["session_seconds"] >> sessionSeconds;
        if (w < 100 || h < 100) return false;
        captureRegion = {x,y,w,h};
        sessionSeconds = std::clamp(sessionSeconds, 1, 24*60*60);
        controls.clear();
        const cv::FileNode nodes = fs["controls"];
        for (const auto& node : nodes) {
            int px=0, py=0;
            std::string side;
            node["x"] >> px; node["y"] >> py; node["side"] >> side;
            if (px < 0 || py < 0 || px >= w || py >= h) continue;
            ControlSide parsed = ControlSide::Unassigned;
            if (side == "left") parsed = ControlSide::Left;
            else if (side == "right") parsed = ControlSide::Right;
            controls.push_back({{px,py}, parsed});
        }
        return true;
    } catch (const cv::Exception&) { return false; }
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
            const char* side = marker.side == ControlSide::Left ? "left" :
                marker.side == ControlSide::Right ? "right" : "unassigned";
            fs << "{" << "x" << marker.point.x << "y" << marker.point.y << "side" << side << "}";
        }
        fs << "]";
        return true;
    } catch (const cv::Exception&) { return false; }
}
}
