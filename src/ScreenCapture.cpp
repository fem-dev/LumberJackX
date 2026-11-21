#include "ScreenCapture.hpp"
#include <opencv2/imgproc.hpp>
#include <stdexcept>

namespace lumberjack {
cv::Mat ScreenCapture::capture(const CaptureRegion& r) const {
    if (r.width <= 0 || r.height <= 0)
        throw std::invalid_argument("Capture dimensions must be positive.");

    HDC screen = GetDC(nullptr);
    if (!screen) throw std::runtime_error("GetDC failed.");

    HDC memory = CreateCompatibleDC(screen);
    if (!memory) {
        ReleaseDC(nullptr, screen);
        throw std::runtime_error("CreateCompatibleDC failed.");
    }

    HBITMAP bitmap = CreateCompatibleBitmap(screen, r.width, r.height);
    if (!bitmap) {
        DeleteDC(memory);
        ReleaseDC(nullptr, screen);
        throw std::runtime_error("CreateCompatibleBitmap failed.");
    }

    HGDIOBJ previousObject = SelectObject(memory, bitmap);
    const BOOL copied = BitBlt(memory, 0, 0, r.width, r.height,
                               screen, r.x, r.y, SRCCOPY | CAPTUREBLT);
    // GetDIBits requires the bitmap not to be selected into a DC.
    SelectObject(memory, previousObject);

    cv::Mat frame;
    if (copied) {
        BITMAPINFO info{};
        info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        info.bmiHeader.biWidth = r.width;
        info.bmiHeader.biHeight = -r.height; // Top-down image.
        info.bmiHeader.biPlanes = 1;
        info.bmiHeader.biBitCount = 32;
        info.bmiHeader.biCompression = BI_RGB;

        frame.create(r.height, r.width, CV_8UC4);
        if (GetDIBits(memory, bitmap, 0, static_cast<UINT>(r.height),
                      frame.data, &info, DIB_RGB_COLORS) == 0) {
            frame.release();
        }
    }

    DeleteObject(bitmap);
    DeleteDC(memory);
    ReleaseDC(nullptr, screen);

    if (frame.empty()) throw std::runtime_error("Screen capture failed.");
    cv::cvtColor(frame, frame, cv::COLOR_BGRA2BGR);
    return frame;
}
}
