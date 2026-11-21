#include "BranchDetector.hpp"
#include "Calibration.hpp"
#include "ScreenCapture.hpp"
#include "Timer.hpp"

#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <windows.h>

#include <algorithm>
#include <cstring>
#include <iostream>
#include <optional>
#include <string>

namespace {
using namespace lumberjack;

constexpr int kToolbarHeight = 58;
constexpr int kFooterHeight = 48;
constexpr int kCanvasMinWidth = 610;
constexpr const char* kConfigPath = "lumberjackx.yml";

struct UiState {
    AppConfig* config{};
    Timer* timer{};
    bool addCircleMode{false};
    bool running{false};
    int selectedMarker{-1};
    std::wstring message{L"تلگرام دسکتاپ را باز کنید و بازی را در محدوده تصویر قرار دهید."};

    cv::Rect addButton{8, 8, 112, 38};
    cv::Rect leftButton{128, 8, 64, 38};
    cv::Rect rightButton{200, 8, 68, 38};
    cv::Rect toggleButton{276, 8, 112, 38};
    cv::Rect saveButton{396, 8, 82, 38};
};

UiState* g_ui = nullptr;

void persist(UiState& ui) {
    if (ui.config->save(kConfigPath)) ui.message = L"تنظیمات در فایل پیکربندی ذخیره شد.";
    else ui.message = L"ذخیره فایل پیکربندی ناموفق بود.";
}

void toggleSession(UiState& ui) {
    if (ui.running) {
        ui.running = false;
        ui.timer->stop();
        ui.message = L"اجرا متوقف شد.";
        return;
    }

    const bool hasLeft = std::any_of(ui.config->controls.begin(), ui.config->controls.end(),
        [](const ControlMarker& marker) { return marker.side == ControlSide::Left; });
    const bool hasRight = std::any_of(ui.config->controls.begin(), ui.config->controls.end(),
        [](const ControlMarker& marker) { return marker.side == ControlSide::Right; });
    if (!hasLeft || !hasRight) {
        ui.message = L"ابتدا دکمه‌های چپ و راست را مشخص کنید.";
        return;
    }

    ui.running = true;
    ui.timer->start(ui.config->sessionSeconds);
    ui.message = L"اجرا آغاز شد؛ منتظر تشخیص معتبر شاخه هستیم.";
}

void onMouse(int event, int x, int y, int, void*) {
    if (!g_ui || event != cv::EVENT_LBUTTONDOWN) return;
    UiState& ui = *g_ui;

    if (y < kToolbarHeight) {
        if (ui.addButton.contains({x,y})) {
            ui.addCircleMode = true;
            ui.message = L"مرکز یکی از دکمه‌های بازی را در تصویر انتخاب کنید.";
        } else if (ui.leftButton.contains({x,y})) {
            if (ui.selectedMarker >= 0) {
                ui.config->controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Left;
                ui.message = L"دکمه انتخاب‌شده به‌عنوان چپ ثبت شد.";
                persist(ui);
            } else ui.message = L"ابتدا یک دایره را انتخاب کنید.";
        } else if (ui.rightButton.contains({x,y})) {
            if (ui.selectedMarker >= 0) {
                ui.config->controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Right;
                ui.message = L"دکمه انتخاب‌شده به‌عنوان راست ثبت شد.";
                persist(ui);
            } else ui.message = L"ابتدا یک دایره را انتخاب کنید.";
        } else if (ui.toggleButton.contains({x,y})) {
            toggleSession(ui);
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
            ui.message = L"دایره انتخاب شد؛ جهت چپ یا راست را تعیین کنید.";
            return;
        }
    }

    if (ui.addCircleMode && x >= 0 && x < ui.config->captureRegion.width &&
        localPoint.y >= 0 && localPoint.y < ui.config->captureRegion.height) {
        ui.config->controls.push_back({localPoint, ControlSide::Unassigned});
        ui.selectedMarker = static_cast<int>(ui.config->controls.size()) - 1;
        ui.addCircleMode = false;
        ui.message = L"دایره اضافه شد؛ جهت آن را مشخص کنید.";
        persist(ui);
    }
}

void drawPersianOverlay(cv::Mat& canvas, const UiState& ui, const std::wstring& status) {
    cv::Mat bgra;
    cv::cvtColor(canvas, bgra, cv::COLOR_BGR2BGRA);
    BITMAPINFO info{};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = bgra.cols;
    info.bmiHeader.biHeight = -bgra.rows;
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    void* pixels = nullptr;
    HBITMAP dib = CreateDIBSection(nullptr, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
    if (!dib || !pixels) { if (dib) DeleteObject(dib); return; }
    std::memcpy(pixels, bgra.data, bgra.total() * bgra.elemSize());
    HDC dc = CreateCompatibleDC(nullptr);
    if (!dc) { DeleteObject(dib); return; }
    HGDIOBJ previousBitmap = SelectObject(dc, dib);
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(255,255,255));
    HFONT font = CreateFontW(-17, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_TT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, L"Segoe UI");
    HGDIOBJ previousFont = font ? SelectObject(dc, font) : nullptr;
    auto drawText = [&](const std::wstring& text, const cv::Rect& rect, UINT flags) {
        RECT r{rect.x, rect.y, rect.x + rect.width, rect.y + rect.height};
        DrawTextW(dc, text.c_str(), static_cast<int>(text.size()), &r,
                  flags | DT_RTLREADING | DT_NOPREFIX | DT_SINGLELINE);
    };
    const UINT centered = DT_CENTER | DT_VCENTER;
    drawText(L"دایره جدید", ui.addButton, centered);
    drawText(L"چپ", ui.leftButton, centered);
    drawText(L"راست", ui.rightButton, centered);
    drawText(ui.running ? L"توقف" : L"شروع", ui.toggleButton, centered);
    drawText(L"ذخیره", ui.saveButton, centered);
    for (const auto& marker : ui.config->controls) {
        const int px = marker.point.x - 14;
        const int py = marker.point.y + kToolbarHeight - 13;
        const std::wstring label = marker.side == ControlSide::Left ? L"چ" :
            marker.side == ControlSide::Right ? L"ر" : L"؟";
        drawText(label, {px, py, 28, 26}, centered);
    }
    drawText(status, {8, canvas.rows - 43, canvas.cols - 16, 20}, DT_RIGHT | DT_VCENTER);
    drawText(ui.message, {8, canvas.rows - 22, canvas.cols - 16, 20}, DT_RIGHT | DT_VCENTER);
    if (previousFont) SelectObject(dc, previousFont);
    if (font) DeleteObject(font);
    SelectObject(dc, previousBitmap);
    DeleteDC(dc);
    cv::Mat rendered(canvas.rows, canvas.cols, CV_8UC4, pixels);
    cv::cvtColor(rendered, canvas, cv::COLOR_BGRA2BGR);
    DeleteObject(dib);
}

void drawButton(cv::Mat& image, const cv::Rect& rect, bool active=false) {
    const cv::Scalar fill = active ? cv::Scalar(65,135,65) : cv::Scalar(65,75,85);
    cv::rectangle(image, rect, fill, cv::FILLED);
    cv::rectangle(image, rect, cv::Scalar(205,215,225), 1);
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
        std::cerr << "Capture area must be at least 100x100 pixels." << std::endl;
        return 2;
    }

    Timer timer;
    timer.stop();
    ScreenCapture capture;
    BranchDetector detector;
    UiState ui{&config, &timer};
    g_ui = &ui;

    const std::string windowName = "LumberJackX | تلگرام دسکتاپ";
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
            cv::Mat canvas(gameFrame.rows + kToolbarHeight + kFooterHeight, canvasWidth, CV_8UC3,
                           cv::Scalar(28,32,38));

            drawButton(canvas, ui.addButton, ui.addCircleMode);
            drawButton(canvas, ui.leftButton);
            drawButton(canvas, ui.rightButton);
            drawButton(canvas, ui.toggleButton, ui.running);
            drawButton(canvas, ui.saveButton);

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
            }

            const Detection detection = detector.detect(gameFrame);
            std::wstring state = ui.running ? L"وضعیت: در حال اجرا" : L"وضعیت: متوقف";
            if (ui.running && detection.side == BranchSide::Unknown)
                state += L" | تشخیص شاخه هنوز آماده نیست؛ ورودی خودکار غیرفعال است";
            if (ui.running) state += L" | زمان باقی‌مانده: " + std::to_wstring(timer.remainingSeconds()) + L" ثانیه";
            drawPersianOverlay(canvas, ui, state);

            cv::imshow(windowName, canvas);
            const int key = cv::waitKey(25);
            if (key == 27 || key == 'q' || key == 'Q') break;
            if (key == 'a' || key == 'A') {
                ui.addCircleMode = true;
                ui.message = L"مرکز یکی از دکمه‌های بازی را در تصویر انتخاب کنید.";
            }
            if ((key == 'l' || key == 'L') && ui.selectedMarker >= 0) {
                config.controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Left;
                persist(ui);
            }
            if ((key == 'r' || key == 'R') && ui.selectedMarker >= 0) {
                config.controls[static_cast<size_t>(ui.selectedMarker)].side = ControlSide::Right;
                persist(ui);
            }
            if (key == 's' || key == 'S') toggleSession(ui);
            if (ui.running && timer.expired()) {
                ui.running = false;
                timer.stop();
                ui.message = L"زمان به پایان رسید؛ اجرا متوقف شد.";
            }
        }
    } catch (const std::exception& error) {
        std::cerr << "Fatal error: " << error.what() << std::endl;
        cv::destroyAllWindows();
        return 1;
    }

    config.save(kConfigPath);
    cv::destroyAllWindows();
    return 0;
}
