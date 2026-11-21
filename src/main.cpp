#include "BranchDetector.hpp"
#include "DecisionEngine.hpp"
#include "ScreenCapture.hpp"
#include "Timer.hpp"
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

namespace {
using namespace lumberjack;
enum class MarkerSide { Unassigned, Left, Right };
struct Marker { cv::Point point; MarkerSide side{MarkerSide::Unassigned}; };
struct UiState {
  bool addMode{false};
  bool running{false};
  int selected{-1};
  std::vector<Marker> markers;
  cv::Rect addButton{8, 8, 104, 34};
  cv::Rect leftButton{120, 8, 72, 34};
  cv::Rect rightButton{200, 8, 78, 34};
  cv::Rect toggleButton{286, 8, 104, 34};
  int toolbarHeight{52};
};
UiState* g_ui = nullptr;

void mouseHandler(int event, int x, int y, int, void*) {
  if (!g_ui || event != cv::EVENT_LBUTTONDOWN) return;
  auto& ui = *g_ui;
  if (y < ui.toolbarHeight) {
    if (ui.addButton.contains({x,y})) { ui.addMode = true; return; }
    if (ui.leftButton.contains({x,y}) && ui.selected >= 0) {
      ui.markers[static_cast<size_t>(ui.selected)].side = MarkerSide::Left; return;
    }
    if (ui.rightButton.contains({x,y}) && ui.selected >= 0) {
      ui.markers[static_cast<size_t>(ui.selected)].side = MarkerSide::Right; return;
    }
    if (ui.toggleButton.contains({x,y})) { ui.running = !ui.running; return; }
  }
  // Click an existing circle to select it.
  for (int i = static_cast<int>(ui.markers.size()) - 1; i >= 0; --i) {
    if (cv::norm(ui.markers[static_cast<size_t>(i)].point - cv::Point(x, y-ui.toolbarHeight)) <= 24.0) {
      ui.selected = i; ui.addMode = false; return;
    }
  }
  // Add a circle by clicking the desired on-screen game control.
  if (ui.addMode && y >= ui.toolbarHeight) {
    ui.markers.push_back({cv::Point(x, y-ui.toolbarHeight), MarkerSide::Unassigned});
    ui.selected = static_cast<int>(ui.markers.size()) - 1;
    ui.addMode = false;
  }
}

void drawButton(cv::Mat& canvas, const cv::Rect& r, const std::string& label, bool active=false) {
  cv::rectangle(canvas, r, active ? cv::Scalar(70,150,70) : cv::Scalar(75,75,75), cv::FILLED);
  cv::rectangle(canvas, r, cv::Scalar(230,230,230), 1);
  cv::putText(canvas, label, {r.x+6,r.y+23}, cv::FONT_HERSHEY_SIMPLEX, 0.43,
              cv::Scalar(255,255,255), 1, cv::LINE_AA);
}
}

int main(int argc, char** argv) {
  using namespace lumberjack;
  auto arg = [&](const std::string& key, int fallback) {
    for (int i=1; i+1<argc; ++i) if (argv[i] == key) return std::stoi(argv[i+1]);
    return fallback;
  };
  CaptureRegion region{arg("--x",0), arg("--y",0), arg("--width",400), arg("--height",600)};
  Timer timer(arg("--seconds",3600));
  ScreenCapture capture;
  BranchDetector detector;
  DecisionEngine engine;
  UiState ui;
  g_ui = &ui;

  const std::string window = "LumberJackX - Telegram Desktop";
  cv::namedWindow(window, cv::WINDOW_AUTOSIZE);
  cv::setMouseCallback(window, mouseHandler);

  std::cout << "Toolbar: Add circle -> click a game button -> select circle -> assign Left/Right. "
               "Start/Stop toggles the session. Q exits.\n";
  std::cout << "Automation remains safely paused until visual branch detection is calibrated.\n";

  try {
    while (!timer.expired()) {
      cv::Mat game = capture.capture(region);
      cv::Mat canvas(game.rows + ui.toolbarHeight, game.cols, CV_8UC3, cv::Scalar(35,35,35));
      drawButton(canvas, ui.addButton, ui.addMode ? "CLICK GAME" : "ADD CIRCLE", ui.addMode);
      drawButton(canvas, ui.leftButton, "LEFT");
      drawButton(canvas, ui.rightButton, "RIGHT");
      drawButton(canvas, ui.toggleButton, ui.running ? "STOP" : "START", ui.running);
      game.copyTo(canvas(cv::Rect(0, ui.toolbarHeight, game.cols, game.rows)));

      for (size_t i=0; i<ui.markers.size(); ++i) {
        const auto& m = ui.markers[i];
        const cv::Point p(m.point.x, m.point.y + ui.toolbarHeight);
        cv::Scalar outline = m.side == MarkerSide::Left ? cv::Scalar(70,220,70) :
                             m.side == MarkerSide::Right ? cv::Scalar(70,150,255) :
                             cv::Scalar(0,220,255);
        cv::circle(canvas, p, 21, outline, 3, cv::LINE_AA);
        if (static_cast<int>(i) == ui.selected) cv::circle(canvas, p, 25, cv::Scalar(255,255,255), 1);
        const char* tag = m.side == MarkerSide::Left ? "L" : m.side == MarkerSide::Right ? "R" : "?";
        cv::putText(canvas, tag, {p.x-6,p.y+6}, cv::FONT_HERSHEY_SIMPLEX, 0.55, outline, 2);
      }

      const std::string status = ui.running ? "SESSION ON - detector calibration pending" : "SESSION OFF";
      cv::putText(canvas, status, {10, canvas.rows-10}, cv::FONT_HERSHEY_SIMPLEX, 0.43,
                  cv::Scalar(255,255,255), 1, cv::LINE_AA);
      cv::imshow(window, canvas);
      const int key = cv::waitKey(25);
      if (key=='q' || key=='Q' || key==27) break;
      // Keyboard accessibility for the same controls.
      if (key=='a' || key=='A') ui.addMode = true;
      if ((key=='l' || key=='L') && ui.selected >= 0) ui.markers[static_cast<size_t>(ui.selected)].side = MarkerSide::Left;
      if ((key=='r' || key=='R') && ui.selected >= 0) ui.markers[static_cast<size_t>(ui.selected)].side = MarkerSide::Right;
      if (key=='s' || key=='S') ui.running = !ui.running;
    }
  } catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << '\n';
    cv::destroyAllWindows();
    return 1;
  }
  cv::destroyAllWindows();
  return 0;
}
