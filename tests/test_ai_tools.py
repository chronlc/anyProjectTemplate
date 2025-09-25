import os

from scripts.ai_tools import api_client


def test_call_ai_returns_stub_when_network_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv('AI_ENABLE_NETWORK', 'false')
    # reload module to pick up env change if necessary
    # call with a sample prompt
    res = api_client.call_ai('hello world')
    assert isinstance(res, dict)
    assert res['cached'] in (True, False)
    assert 'AI network disabled' in res['text']


def test_cache_set_get(tmp_path, monkeypatch):
    # use a local db path
    db = tmp_path / 'cache.sqlite'
    monkeypatch.setenv('AI_CACHE_DB', str(db))
    from scripts.ai_tools.cache import PromptCache

    c = PromptCache(str(db))
    c.set('k', 'v')
    assert c.get('k') == 'v'
