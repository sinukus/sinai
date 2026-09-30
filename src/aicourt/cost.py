from dataclasses import dataclass
from .types import Model

@dataclass(frozen=True)
class Budget:
    max_usd: float = 0.10
    target_confidence: float = 0.90

class CostController:
    def __init__(self, models: list[Model], budget: Budget = Budget()):
        self.models, self.budget = models, budget

    def candidates(self, capability="general"):
        eligible = [m for m in self.models if capability in m.capabilities]
        return sorted(eligible, key=lambda m:
            (m.input_per_million+m.output_per_million)/max(m.quality, .01))

    def independent(self, capability="general", n=3):
        out, families = [], set()
        for m in self.candidates(capability):
            if m.family not in families:
                out.append(m); families.add(m.family)
            if len(out) == n: break
        return out

    def can_spend(self, spent, increment):
        return spent + increment <= self.budget.max_usd
