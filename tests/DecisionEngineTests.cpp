#include "BranchDetector.hpp"
#include "Calibration.hpp"
#include "DecisionEngine.hpp"

#include <opencv2/core.hpp>
#include <cstdio>
#include <string>

int main() {
    using namespace lumberjack;

    const DecisionEngine engine;
    if (engine.choose(BranchSide::Left) != Move::Right) return 1;
    if (engine.choose(BranchSide::Right) != Move::Left) return 2;
    if (engine.choose(BranchSide::Unknown) != Move::Wait) return 3;

    const BranchDetector detector;
    const cv::Mat sample(120, 80, CV_8UC3, cv::Scalar(0,0,0));
    const Detection result = detector.detect(sample);
    if (result.side != BranchSide::Unknown || result.confidence != 0.0) return 4;

    const std::string path = "lumberjackx-test-config.yml";
    AppConfig original;
    original.captureRegion = {15, 25, 420, 680};
    original.sessionSeconds = 125;
    original.controls = {
        {{90, 500}, ControlSide::Left},
        {{320, 500}, ControlSide::Right},
        {{210, 480}, ControlSide::Unassigned}
    };
    if (!original.save(path)) return 5;

    AppConfig loaded;
    if (!loaded.load(path)) { std::remove(path.c_str()); return 6; }
    std::remove(path.c_str());

    if (loaded.captureRegion.x != original.captureRegion.x ||
        loaded.captureRegion.y != original.captureRegion.y ||
        loaded.captureRegion.width != original.captureRegion.width ||
        loaded.captureRegion.height != original.captureRegion.height) return 7;
    if (loaded.sessionSeconds != original.sessionSeconds) return 8;
    if (loaded.controls.size() != original.controls.size()) return 9;
    if (loaded.controls[0].side != ControlSide::Left) return 10;
    if (loaded.controls[1].side != ControlSide::Right) return 11;
    if (loaded.controls[2].side != ControlSide::Unassigned) return 12;
    return 0;
}
