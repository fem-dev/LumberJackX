#include "Timer.hpp"
#include <algorithm>
namespace lumberjack {
Timer::Timer(int seconds) : deadline_(std::chrono::steady_clock::now() + std::chrono::seconds(std::max(0, seconds))) {}
bool Timer::expired() const { return std::chrono::steady_clock::now() >= deadline_; }
int Timer::remainingSeconds() const {
  auto n = std::chrono::duration_cast<std::chrono::seconds>(deadline_ - std::chrono::steady_clock::now()).count();
  return static_cast<int>(std::max<std::int64_t>(0, n));
}
}
