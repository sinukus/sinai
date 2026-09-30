from dataclasses import dataclass, field
from typing import FrozenSet

@dataclass(frozen=True)
class Model:
    id: str
    family: str
    input_per_million: float
    output_per_million: float
    quality: float
    capabilities: FrozenSet[str] = field(default_factory=lambda: frozenset({"general"}))

@dataclass(frozen=True)
class Answer:
    model: Model
    text: str
    input_tokens: int
    output_tokens: int
    confidence: float = 0.5

    @property
    def cost_usd(self) -> float:
        return (self.input_tokens*self.model.input_per_million +
                self.output_tokens*self.model.output_per_million)/1_000_000
