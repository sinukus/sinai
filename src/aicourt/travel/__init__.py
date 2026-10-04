"""Local destination preparation, independent of speech and model providers."""
from dataclasses import dataclass
from importlib.resources import files
import json
import re
from pathlib import Path
from typing import Protocol


class LanguageResources(Protocol):
    async def ensure(self, locale: str, component: str) -> str:
        """Return ready, pending, requires_user_action, or unsupported.

        Native adapters initiate supported OS downloads and verify installation.
        Never return ready merely because a download was requested.
        """
        ...


@dataclass
class Destination:
    code: str
    country: str
    locales: list[str]
    city: str | None = None


class TravelHelper:
    def __init__(self, storage: Path, resources: LanguageResources | None = None,
                 pack_directory: Path | None = None, language_template: Path | None = None):
        self.storage = Path(storage)
        self.resources = resources
        self.pack_directory = pack_directory
        self.language_template = language_template

    def packs(self):
        root = self.pack_directory or files(__package__).joinpath('packs')
        packs = [json.loads(p.read_text(encoding='utf-8')) for p in root.iterdir()
                 if p.name.endswith('.json')]
        for pack in packs:
            for key in ('code', 'country', 'aliases', 'locales'):
                if key not in pack:
                    raise ValueError(f'Country pack missing {key}')
            if not re.fullmatch(r'[A-Z]{2}', pack['code']):
                raise ValueError('Country codes must be two uppercase letters')
        return packs

    def resolve(self, prompt: str) -> dict:
        # Narrow intent detection: do not interpret any mention of a country as a trip.
        match = re.fullmatch(r"\s*(?:I am|I'm|I’m)\s+(?:going|travelling|traveling)\s+to\s+(.+?)[.!]?\s*", prompt, re.I)
        if not match:
            raise ValueError('Use a destination prompt such as "I am going to Japan"')
        name = match.group(1).strip().casefold()
        matches = [p for p in self.packs()
                   if name in {p['country'].casefold(), p['code'].casefold(),
                               *(a.casefold() for a in p['aliases'])}]
        if len(matches) != 1:
            raise ValueError('Destination unavailable or ambiguous; install its country pack')
        return matches[0]

    async def prepare(self, prompt: str, city: str | None = None) -> dict:
        pack = self.resolve(prompt)
        target = self.storage / pack['code']
        target.mkdir(parents=True, exist_ok=True)
        template = files(__package__).joinpath('templates/travel.txt').read_text(encoding='utf-8')
        (target / 'travel.txt').write_text(template, encoding='utf-8')
        language = (self.language_template.read_text(encoding='utf-8')
                    if self.language_template is not None else
                    files(__package__).joinpath('templates/language.md').read_text(encoding='utf-8'))
        (target / 'language.txt').write_text(language, encoding='utf-8')
        state = {'destination': Destination(pack['code'], pack['country'], pack['locales'], city).__dict__,
                 'travel_template': 'ready',
                 'language_template': 'ready' if language is not None else 'missing',
                 'guidance': 'not_downloaded', 'resources': {}}
        for locale in pack['locales']:
            state['resources'][locale] = {}
            for component in ('speech_to_text', 'text_to_speech', 'translation'):
                status = 'adapter_missing'
                if self.resources is not None:
                    try:
                        status = await self.resources.ensure(locale, component)
                        if status not in {'ready', 'pending', 'requires_user_action', 'unsupported'}:
                            raise ValueError('Invalid resource status')
                    except Exception:
                        status = 'failed'
                state['resources'][locale][component] = status
        (target / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        (target / 'country.json').write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding='utf-8')
        return state

    def build_prompt(self, country_code: str, question: str) -> str:
        if not re.fullmatch(r'[A-Z]{2}', country_code):
            raise ValueError('Invalid country code')
        target = self.storage / country_code
        state = json.loads((target / 'state.json').read_text(encoding='utf-8'))
        travel = (target / 'travel.txt').read_text(encoding='utf-8')
        language_file = target / 'language.txt'
        language = language_file.read_text(encoding='utf-8') if language_file.exists() else 'Canonical language template unavailable. Do not reconstruct it.'
        return ('Help a technically experienced Western traveler understand local systems. '
                'First explain what the system is, the local convention and relevant difference; '
                'then give exact actions. Avoid stereotypes and do not infer lock operation from country alone. '
                'Ask for a photo or model when necessary. State uncertainty. Prices in USD first. '
                'Current laws, prices and schedules require retrieved evidence; if offline, say unverified. '
                'Answer the immediate question; use the full template only for a requested full guide.\n'
                f'DESTINATION: {json.dumps(state["destination"])}\n'
                f'TRAVEL TEMPLATE:\n{travel}\nLANGUAGE TEMPLATE:\n{language}\nQUESTION:\n{question}')

    async def answer(self, court, country_code: str, question: str):
        return await court.answer(self.build_prompt(country_code, question))
