#include "BranchDetector.hpp"
#include "Calibration.hpp"
#include "ScreenCapture.hpp"
#include "Timer.hpp"

#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <windows.h>

#include <algorithm>
#include <iostream>
#include <optional>
#include <string>

namespace {
using namespace lumberjack;

constexpr int kToolbarHeight = 58;
constexpr int kCanvasMinWidth = 610;
constexpr const char* kConfigPath = "lumberjackx.yml";

struct UiState {
    AppConfig* config{};
    Timer* timer{};
    bool addCircleMode{false};
    bool running{false};
    int selectedMarker{-1};
    std::string message{"Load Telegram Desktop and position the game inside the capture area."};

    cv::Rect addButton{8, 8, 112, 38};
    cv::Rect leftButton{128, 8, 72, 38};
    cv::Rect rightButton{208, 8, 78, 38};
    cv::Rect toggleButton{294, 8, 112, 38};
    cv::Rect saveButton{414, 8, 82, 38};
};

UiState* g_ui = nullptr;

void persist(UiState& ui) {
    if (ui.config->save(kConfigPath)) ui.message = "Calibration saved to lumberjackx.yml";
    else ui.message = "Could not save lumberjackx.yml";
}

void onMouse(int event, int x, int y, int, void*) {
    if (!g_ui || event != cv::EVENT_LBUTTONDOWN) return;
    UiState& ui = *g_ui;

    if (y < kToolbarHeight) {
        if (ui.addButton.contains({x,y})) {
            ui.addCircleMode = true;
            ui.message = "Click the center of a game control in the preview.";
        } else if (ui.leftButton.contains({x,y})) {
            if (ui.selectedMarker >= 0) {
                ui.config->controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Left;
                ui.message = "Selected control assigned: LEFT";
                persist(ui);
            } else ui.message = "Select a circle first.";
        } else if (ui.rightButton.contains({x,y})) {
            if (ui.selectedMarker >= 0) {
                ui.config->controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Right;
                ui.message = "Selected control assigned: RIGHT";
                persist(ui);
            } else ui.message = "Select a circle first.";
        } else if (ui.toggleButton.contains({x,y})) {
            if (!ui.running) {
                const bool hasLeft = std::any_of(ui.config->controls.begin(), ui.config->controls.end(),
                    [](const ControlMarker& m) { return m.side == ControlSide::Left; });
                const bool hasRight = std::any_of(ui.config->controls.begin(), ui.config->controls.end(),
                    [](const ControlMarker& m) { return m.side == ControlSide::Right; });
                if (!hasLeft || !hasRight) {
                    ui.message = "Add and label both LEFT and RIGHT controls before starting.";
                    return;
                }
                ui.running = true;
                ui.timer->start(ui.config->sessionSeconds);
                ui.message = "Session started. Waiting for validated branch recognition.";
            } else {
                ui.running = false;
                ui.timer->stop();
                ui.message = "Session stopped.";
            }
        } else if (ui.saveButton.contains({x,y})) {
            persist(ui);
        }
        return;
    }

    const cv::Point localPoint{x, y - kToolbarHeight};
    // Select the topmost marker if the user clicked an existing circle.
    for (int i = static_cast<int>(ui.config->controls.size()) - 1; i >= 0; --i) {
        const auto& marker = ui.config->controls[static_cast<size_t>(i)];
        if (cv::norm(marker.point - localPoint) <= 23.0) {
            ui.selectedMarker = i;
            ui.addCircleMode = false;
            ui.message = "Marker selected. Assign LEFT or RIGHT, or drag is not required.";
            return;
        }
    }

    if (ui.addCircleMode && x >= 0 && x < ui.config->captureRegion.width &&
        localPoint.y >= 0 && localPoint.y < ui.config->captureRegion.height) {
        ui.config->controls.push_back({localPoint, ControlSide::Unassigned});
        ui.selectedMarker = static_cast<int>(ui.config->controls.size()) - 1;
        ui.addCircleMode = false;
        ui.message = "Circle added. Choose LEFT or RIGHT to label it.";
        persist(ui);
    }
}

void drawButton(cv::Mat& image, const cv::Rect& rect, const std::string& label, bool active=false) {
    const cv::Scalar fill = active ? cv::Scalar(65,135,65) : cv::Scalar(65,75,85);
    cv::rectangle(image, rect, fill, cv::FILLED);
    cv::rectangle(image, rect, cv::Scalar(205,215,225), 1);
    int baseline = 0;
    const auto size = cv::getTextSize(label, cv::FONT_HERSHEY_SIMPLEX, 0.43, 1, &baseline);
    const cv::Point origin{rect.x + (rect.width-size.width)/2, rect.y + (rect.height+size.height)/2};
    cv::putText(image, label, origin, cv::FONT_HERSHEY_SIMPLEX, 0.43,
                cv::Scalar(255,255,255), 1, cv::LINE_AA);
}

std::optional<int> argument(int argc, char** argv, const std::string& name) {
    for (int i=1; i+1<argc; ++i) {
        if (argv[i] == name) {
            try { return std::stoi(argv[i+1]); }
            catch (...) { return std::nullopt; }
        }
    }
    return std::nullopt;
}
}

int main(int argc, char** argv) {
    using namespace lumberjack;
    SetProcessDPIAware();

    AppConfig config;
    config.load(kConfigPath);
    if (auto v=argument(argc,argv,"--x")) config.captureRegion.x=*v;
    if (auto v=argument(argc,argv,"--y")) config.captureRegion.y=*v;
    if (auto v=argument(argc,argv,"--width")) config.captureRegion.width=*v;
    if (auto v=argument(argc,argv,"--height")) config.captureRegion.height=*v;
    if (auto v=argument(argc,argv,"--seconds")) config.sessionSeconds=std::clamp(*v,1,24*60*60);

    if (config.captureRegion.width < 100 || config.captureRegion.height < 100) {
        std::cerr << "Capture region must be at least 100 x 100 pixels.\n";
        return 2;
    }

    Timer timer;
    timer.stop();
    ScreenCapture capture;
    BranchDetector detector;
    UiState ui{&config, &timer};
    g_ui = &ui;

    const std::string windowName = "LumberJackX | Telegram Desktop";
    cv::namedWindow(windowName, cv::WINDOW_AUTOSIZE);
    cv::setMouseCallback(windowName, onMouse);

    std::cout << "LumberJackX v0.2 - Windows 10\n"
              << "ADD CIRCLE: click a game control in the preview.\n"
              << "Select a circle, then assign LEFT or RIGHT.\n"
              << "START/STOP toggles the session. Q or ESC exits.\n";

    try {
        while (true) {
            cv::Mat gameFrame = capture.capture({
                config.captureRegion.x, config.captureRegion.y,
                config.captureRegion.width, config.captureRegion.height
            });

            const int canvasWidth = std::max(kCanvasMinWidth, gameFrame.cols);
            cv::Mat canvas(gameFrame.rows + kToolbarHeight, canvasWidth, CV_8UC3,
                           cv::Scalar(28,32,38));

            drawButton(canvas, ui.addButton, ui.addCircleMode ? "CLICK GAME" : "ADD CIRCLE", ui.addCircleMode);
            drawButton(canvas, ui.leftButton, "LEFT");
            drawButton(canvas, ui.rightButton, "RIGHT");
            drawButton(canvas, ui.toggleButton, ui.running ? "STOP" : "START", ui.running);
            drawButton(canvas, ui.saveButton, "SAVE");

            gameFrame.copyTo(canvas(cv::Rect(0,kToolbarHeight,gameFrame.cols,gameFrame.rows)));

            for (size_t i=0; i<config.controls.size(); ++i) {
                const auto& marker = config.controls[i];
                const cv::Point p{marker.point.x, marker.point.y+kToolbarHeight};
                const cv::Scalar color = marker.side == ControlSide::Left ? cv::Scalar(80,220,100) :
                    marker.side == ControlSide::Right ? cv::Scalar(80,170,255) :
                    cv::Scalar(0,220,255);
                cv::circle(canvas, p, 22, color, 2, cv::LINE_AA);
                if (static_cast<int>(i) == ui.selectedMarker)
                    cv::circle(canvas, p, 27, cv::Scalar(245,245,245), 1, cv::LINE_AA);
                const char* markerLabel = marker.side == ControlSide::Left ? "L" :
                    marker.side == ControlSide::Right ? "R" : "?";
                cv::putText(canvas, markerLabel,
                            {p.x-6,p.y+6}, cv::FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv::LINE_AA);
            }

            const Detection detection = detector.detect(gameFrame);
            std::string state = ui.running ? "SESSION ON" : "SESSION OFF";
            if (ui.running && detection.side == BranchSide::Unknown)
                state += " | DETECTOR NOT CALIBRATED - NO INPUT";
            if (ui.running) state += " | " + std::to_string(timer.remainingSeconds()) + "s";
            cv::putText(canvas, state, {10,canvas.rows-25}, cv::FONT_HERSHEY_SIMPLEX,
                        0.43, cv::Scalar(245,245,245), 1, cv::LINE_AA);
            cv::putText(canvas, ui.message, {10,canvas.rows-8}, cv::FONT_HERSHEY_SIMPLEX,
                        0.36, cv::Scalar(190,205,215), 1, cv::LINE_AA);

            cv::imshow(windowName, canvas);
            const int key = cv::waitKey(25);
            if (key == 27 || key == 'q' || key == 'Q') break;
            if (key == 'a' || key == 'A') {
                ui.addCircleMode = true;
                ui.message = "Click the center of a game control in the preview.";
            }
            if ((key == 'l' || key == 'L') && ui.selectedMarker >= 0) {
                config.controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Left;
                persist(ui);
            }
            if ((key == 'r' || key == 'R') && ui.selectedMarker >= 0) {
                config.controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Right;
                persist(ui);
            }
            if (key == 's' || key == 'S') {
                ui.running = !ui.running;
                if (ui.running) timer.start(config.sessionSeconds);
                else timer.stop();
            }
            if (ui.running && timer.expired()) {
                ui.running = false;
                timer.stop();
                ui.message = "Session timer finished. Session stopped.";
            }
        }
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << '\n';
        cv::destroyAllWindows();
        return 1;
    }

    config.save(kConfigPath);
    cv::destroyAllWindows();
    return 0;
}
