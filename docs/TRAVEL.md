# Global travel helper: local-first foundation

Country packs are data plugins, not executable code. Japan and Vietnam are initial packs, not hard-coded limits. Supply a pack directory to add other countries. Locale availability is verified by each platform adapter, never inferred from the country.

```python
from pathlib import Path
from aicourt.travel import TravelHelper

helper = TravelHelper(Path('local-travel'), resources=native_adapter)
status = await helper.prepare("I'm going to Japan")
answer = await helper.answer(court, 'JP', 'How do I use this ticket machine?')
```

The exact full 25-section travel template is bundled from sinukus/Travel_prompt, blob 76a95cbdf6bfd7bceefb5017279fc14eaf647e68. It remains the shared base. The bundled language template was recreated from the user's specification: 30 words, 60 phrases and 90 sentences. It is not a recovered original. A supplied language_template path overrides the bundled text verbatim.

STT, TTS and translation are distinct resources. Selecting a destination invokes all three adapters. Each native adapter must use supported platform APIs to request downloads, and surface required OS prompts or settings. Availability varies by device and locale. Native adapters must return ready only after verification. They are not implemented here.

Local state and templates are available without a network. Destination guidance retrieval, native mobile clients, microphone/photo input, native adapters, and an actual offline model backend remain to be implemented. The repository currently supplies a mock model backend, so this change does not claim working AI answers or full offline conversation. Unsupported or pending resources never silently fall back to cloud.

An intent recognizer in a future client can call prepare with a canonical destination prompt. The current parser deliberately accepts only explicit simple destination statements; it does not guess arbitrary language, dates, or cities.
