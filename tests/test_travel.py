import json
import pytest
from aicourt.travel import TravelHelper


@pytest.mark.asyncio
async def test_local_preparation_and_missing_resources(tmp_path):
    helper = TravelHelper(tmp_path)
    state = await helper.prepare("I'm going to Japan")
    assert state['destination']['code'] == 'JP'
    assert state['language_template'] == 'ready'
    assert state['resources']['ja-JP']['speech_to_text'] == 'adapter_missing'
    prompt = helper.build_prompt('JP', 'How does this door lock work?')
    assert '25. Travel Etiquette' in prompt
    assert 'W001' in prompt and 'S090' in prompt
    with pytest.raises(ValueError):
        helper.build_prompt('../', 'q')


@pytest.mark.asyncio
async def test_independent_resource_status_and_language(tmp_path):
    class Resources:
        async def ensure(self, locale, component):
            return {'speech_to_text':'pending', 'text_to_speech':'ready',
                    'translation':'requires_user_action'}[component]
    language = tmp_path / 'canonical.txt'
    language.write_text('Exact user template')
    state = await TravelHelper(tmp_path / 'data', Resources(), language_template=language).prepare('I am going to Vietnam')
    assert state['language_template'] == 'ready'
    assert state['resources']['vi-VN'] == {'speech_to_text':'pending', 'text_to_speech':'ready', 'translation':'requires_user_action'}


@pytest.mark.asyncio
async def test_external_country_pack_and_failed_download(tmp_path):
    packs = tmp_path / 'packs'
    packs.mkdir()
    (packs / 'BR.json').write_text(json.dumps({'code':'BR','country':'Brazil','aliases':[], 'locales':['pt-BR']}))
    class Broken:
        async def ensure(self, locale, component):
            raise OSError('offline')
    helper = TravelHelper(tmp_path / 'data', Broken(), packs)
    assert (await helper.prepare('I am going to Brazil'))['resources']['pt-BR']['translation'] == 'failed'
    with pytest.raises(ValueError):
        helper.resolve('I am not going to Brazil')
