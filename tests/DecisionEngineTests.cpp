#include "BranchDetector.hpp"
#include "DecisionEngine.hpp"

#include <opencv2/core.hpp>
#include <cassert>

int main() {
    using namespace lumberjack;

    const DecisionEngine engine;
    assert(engine.choose(BranchSide::Left) == Move::Right);
    assert(engine.choose(BranchSide::Right) == Move::Left);
    assert(engine.choose(BranchSide::Unknown) == Move::Wait);

    const BranchDetector detector;
    const cv::Mat sample(120, 80, CV_8UC3, cv::Scalar(0,0,0));
    const Detection result = detector.detect(sample);
    assert(result.side == BranchSide::Unknown);
    assert(result.confidence == 0.0);

    return 0;
}
