#pragma once
#include <chrono>
namespace lumberjack {
class Timer {
public:
  explicit Timer(int seconds = 3600);
  void start(int seconds);
  void stop();
  bool running() const;
  bool expired() const;
  int remainingSeconds() const;
private:
  std::chrono::steady_clock::time_point deadline_{};
  bool running_{false};
};
}
