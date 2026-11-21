#include "GameController.hpp"
#include <windows.h>
namespace lumberjack {
bool GameController::clickAt(const cv::Point& point) const {
  POINT previous{};
  const bool restore = GetCursorPos(&previous) != 0;
  if (!SetCursorPos(point.x, point.y)) return false;
  INPUT events[2]{};
  events[0].type = INPUT_MOUSE; events[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
  events[1].type = INPUT_MOUSE; events[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;
  const bool ok = SendInput(2, events, sizeof(INPUT)) == 2;
  if (restore) SetCursorPos(previous.x, previous.y);
  return ok;
}
}
