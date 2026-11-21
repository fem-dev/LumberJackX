#pragma once
#include <chrono>
namespace lumberjack {
class Timer {
public:
  explicit Timer(int seconds);
  bool expired() const;
  int remainingSeconds() const;
private:
  std::chrono::steady_clock::time_point deadline_;
};
}
