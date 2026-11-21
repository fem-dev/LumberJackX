#include "BranchDetector.hpp"
#include "DecisionEngine.hpp"
#include "ScreenCapture.hpp"
#include "Timer.hpp"
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <string>
namespace {
int arg(int argc, char** argv, const std::string& key, int fallback) {
  for (int i=1; i+1<argc; ++i) if (argv[i] == key) return std::stoi(argv[i+1]);
  return fallback;
}
}
int main(int argc, char** argv) {
  using namespace lumberjack;
  CaptureRegion region{arg(argc,argv,"--x",0), arg(argc,argv,"--y",0),
                       arg(argc,argv,"--width",400), arg(argc,argv,"--height",600)};
  Timer timer(arg(argc,argv,"--seconds",60));
  ScreenCapture capture; BranchDetector detector; DecisionEngine engine;
  std::cout << "LumberJackX capture preview. Press Q to quit. Detector is not calibrated; no keys are sent.\n";
  try {
    while (!timer.expired()) {
      cv::Mat frame = capture.capture(region);
      Move move = engine.choose(detector.detect(frame));
      cv::putText(frame, "Time: " + std::to_string(timer.remainingSeconds()) +
        "s | " + (move == Move::Wait ? "UNCALIBRATED" : "READY"),
        cv::Point(10,25), cv::FONT_HERSHEY_SIMPLEX, 0.55, cv::Scalar(20,20,20), 2);
      cv::imshow("LumberJackX - capture preview", frame);
      int key = cv::waitKey(30);
      if (key=='q' || key=='Q' || key==27) break;
    }
  } catch (const std::exception& e) { std::cerr << "Error: " << e.what() << '\n'; return 1; }
  cv::destroyAllWindows();
  std::cout << "Session ended.\n";
  return 0;
}
