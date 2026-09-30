import asyncio

class Court:
    def __init__(self, backend, controller):
        self.backend, self.controller = backend, controller

    async def answer(self, question, capability="general"):
        models = self.controller.independent(capability, 3)
        if not models:
            raise ValueError(f"No model supports {capability!r}")

        first = await self.backend.ask(models[0], self._witness(question))
        if first.confidence >= self.controller.budget.target_confidence:
            return first.text

        rest = await asyncio.gather(*[
            self.backend.ask(m, self._witness(question)) for m in models[1:]
        ])
        witnesses = [first, *rest]
        testimony = "\n\n".join(
            f"WITNESS {i+1}:\n{x.text}" for i,x in enumerate(witnesses)
        )

        critiques = await asyncio.gather(*[
            self.backend.ask(x.model, self._critique(question, testimony))
            for x in witnesses
        ])
        critique_text = "\n\n".join(
            f"CROSS-EXAM {i+1}:\n{x.text}" for i,x in enumerate(critiques)
        )
        judge = max(self.controller.candidates(capability), key=lambda m:m.quality)
        result = await self.backend.ask(
            judge, self._judge(question, testimony, critique_text)
        )
        return result.text

    @staticmethod
    def _witness(q):
        return ("Answer independently. Do not assume the premise is correct. "
                "Separate verified fact from inference. Say UNKNOWN rather than invent.\n"
                f"QUESTION:\n{q}")

    @staticmethod
    def _critique(q, testimony):
        return ("Adversarially fact-check these anonymous answers. Identify factual "
                "errors, unsupported claims, contradictions and evidence needed. "
                "Do not use majority vote.\n"
                f"QUESTION:\n{q}\nTESTIMONY:\n{testimony}")

    @staticmethod
    def _judge(q, testimony, critiques):
        return ("Produce ONE user-facing answer. Evidence outranks consensus. "
                "Do not expose internal deliberation. State unresolved uncertainty; "
                "never manufacture consensus.\n"
                f"QUESTION:\n{q}\nTESTIMONY:\n{testimony}\nCRITIQUES:\n{critiques}")
