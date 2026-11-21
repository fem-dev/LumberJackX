#include "GameController.hpp"
#include <windows.h>
namespace lumberjack {
bool GameController::press(Move move, unsigned int holdMilliseconds) const {
  WORD key = move == Move::Left ? VK_LEFT : move == Move::Right ? VK_RIGHT : 0;
  if (!key) return true;
  INPUT down{}; down.type = INPUT_KEYBOARD; down.ki.wVk = key;
  if (SendInput(1, &down, sizeof(INPUT)) != 1) return false;
  Sleep(holdMilliseconds);
  INPUT up{}; up.type = INPUT_KEYBOARD; up.ki.wVk = key; up.ki.dwFlags = KEYEVENTF_KEYUP;
  return SendInput(1, &up, sizeof(INPUT)) == 1;
}
}
