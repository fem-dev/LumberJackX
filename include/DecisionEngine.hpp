#pragma once
#include "BranchDetector.hpp"
namespace lumberjack {
enum class Move { Left, Right, Wait };
class DecisionEngine { public: Move choose(BranchSide hazard) const; };
}
