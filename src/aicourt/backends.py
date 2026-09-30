from typing import Protocol
from .types import Model, Answer

class Backend(Protocol):
    async def ask(self, model: Model, prompt: str) -> Answer: ...

class MockBackend:
    def __init__(self, response="mock answer", confidence=0.9):
        self.response, self.confidence, self.calls = response, confidence, []
    async def ask(self, model, prompt):
        self.calls.append((model, prompt))
        return Answer(model, self.response, 100, 50, self.confidence)
