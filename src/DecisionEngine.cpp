#include "DecisionEngine.hpp"
namespace lumberjack {
Move DecisionEngine::choose(BranchSide hazard) const {
  switch (hazard) {
    case BranchSide::Left: return Move::Right;
    case BranchSide::Right: return Move::Left;
    case BranchSide::None: return Move::Left;
    default: return Move::Wait;
  }
}
}
