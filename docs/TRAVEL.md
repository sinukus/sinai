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

Local state and templates are available without a network. Destination guidance retrieval, native mobile clients, microphone/photo input, native adapters, remain to be implemented. A real local Ollama transport is available for text responses; native voice conversation is not implemented. Unsupported or pending resources never silently fall back to cloud.

An intent recognizer in a future client can call prepare with a canonical destination prompt. The current parser deliberately accepts only explicit simple destination statements; it does not guess arbitrary language, dates, or cities.

## Run the local text app

Install this project with `python -m pip install -e .`. Install and run Ollama separately, with a model suitable for your machine already downloaded. Then run:

```sh
sinai-travel --model YOUR_INSTALLED_MODEL
```

Open `http://127.0.0.1:8765`. Enter a destination statement, then a question. The HTTP response pushes newline-delimited destination, text-delta, completion and error events as they occur; the browser consumes the response stream without polling. The Ollama chat transport is implemented against https://docs.ollama.com/api/chat. No API key or cloud service is used, and no model is downloaded automatically.

The app uses the configured local model directly; it bypasses the legacy multi-model Court orchestration. History and destination selection persist in atomic JSON files. SQLite is no longer used by LocalMemory; existing databases are left untouched and not migrated automatically. The server binds to loopback only and rejects cross-site browser requests. It is a single-user desktop prototype, not an exposed network service or a native iOS/Android app.

The previous missing-backend limitation is addressed by the real Ollama transport. Native mobile speech, translation downloads, photo input and sourced guidance remain unfinished. Tests cover a real HTTP streaming fixture, gateway requests, state persistence, cross-site rejection and failed generation. They do not verify the quality of a downloaded model or claim device-level voice functionality.
