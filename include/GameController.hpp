#pragma once
#include "DecisionEngine.hpp"
namespace lumberjack {
class GameController { public: bool press(Move move, unsigned int holdMilliseconds = 35) const; };
}
