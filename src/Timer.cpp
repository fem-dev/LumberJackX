#include "Timer.hpp"
#include <algorithm>
#include <cstdint>
namespace lumberjack {
Timer::Timer(int seconds) { start(seconds); }
void Timer::start(int seconds) {
  deadline_ = std::chrono::steady_clock::now() +
      std::chrono::seconds(std::clamp(seconds, 1, 24*60*60));
  running_ = true;
}
void Timer::stop() { running_ = false; }
bool Timer::running() const { return running_; }
bool Timer::expired() const { return running_ && std::chrono::steady_clock::now() >= deadline_; }
int Timer::remainingSeconds() const {
  if (!running_) return 0;
  const auto n = std::chrono::duration_cast<std::chrono::seconds>(
      deadline_ - std::chrono::steady_clock::now()).count();
  return static_cast<int>(std::max<std::int64_t>(0, n));
}
}
