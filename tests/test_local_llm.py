"""Tests for the local LM Studio lifecycle and its integration points.

Everything is mocked: no real server, no real lms CLI, no network. Covers
backend/local_llm.py, the lmstudio provider in backend/prompt_builder.py,
and the local-first path in backend/ai_advisor.py and backend/stl_verifier.py.
"""

import json
from unittest import mock

import pytest

from backend.local_llm import (
    DEFAULT_MODEL,
    LMSTUDIO_API,
    LMSTUDIO_MODEL,
    chat,
    chat_vision,
    ensure_gemma,
    find_lms_cli,
    list_loaded_models,
    load_model,
    server_ready,
    start_server,
)


# ── lms CLI discovery ────────────────────────────────────────────────────

def test_find_lms_cli_env_override(tmp_path):
    fake = tmp_path / "lms.exe"
    fake.write_bytes(b"MZ")
    with mock.patch.dict("os.environ", {"LMSTUDIO_BIN": str(fake)}, clear=False):
        assert find_lms_cli() == str(fake)


def test_find_lms_cli_none_when_missing(tmp_path):
    with mock.patch("backend.local_llm.Path.home",
                    return_value=tmp_path), \
         mock.patch("backend.local_llm.shutil.which", return_value=None):
        assert find_lms_cli() is None


# ── server / model lifecycle ─────────────────────────────────────────────

def _fake_response(payload, status=200):
    resp = mock.MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__.return_value = resp
    return resp


def test_server_ready_true():
    with mock.patch("urllib.request.urlopen", return_value=_fake_response({"data": []})):
        assert server_ready() is True


def test_server_ready_false_on_error():
    with mock.patch("urllib.request.urlopen", side_effect=OSError("refused")):
        assert server_ready() is False


def test_list_loaded_models():
    payload = {"data": [{"id": "google/gemma-4-12b"}, {"id": "other"}]}
    with mock.patch("urllib.request.urlopen", return_value=_fake_response(payload)):
        assert list_loaded_models() == ["google/gemma-4-12b", "other"]


def test_list_loaded_models_empty_on_error():
    with mock.patch("urllib.request.urlopen", side_effect=OSError("refused")):
        assert list_loaded_models() == []


def test_start_server_skips_when_ready():
    with mock.patch("backend.local_llm.server_ready", return_value=True) as ready, \
         mock.patch("backend.local_llm._run_lms") as run:
        assert start_server() is True
        ready.assert_called_once()
        run.assert_not_called()


def test_start_server_polls_until_ready():
    ready_states = iter([False, False, True])
    with mock.patch("backend.local_llm.server_ready",
                    side_effect=lambda *a, **k: next(ready_states)) as ready, \
         mock.patch("backend.local_llm._run_lms", return_value=True) as run, \
         mock.patch("backend.local_llm.time.sleep"):
        assert start_server() is True
        run.assert_called_once_with(["server", "start"], timeout=30)


def test_load_model_idempotent_when_already_loaded():
    with mock.patch("backend.local_llm.list_loaded_models",
                    return_value=[LMSTUDIO_MODEL]), \
         mock.patch("backend.local_llm._run_lms") as run:
        assert load_model() is True
        run.assert_not_called()


def test_load_model_runs_cli_and_polls():
    with mock.patch("backend.local_llm.list_loaded_models",
                    side_effect=[[], [], [LMSTUDIO_MODEL]]) as listed, \
         mock.patch("backend.local_llm._run_lms", return_value=True) as run, \
         mock.patch("backend.local_llm.time.sleep"):
        assert load_model() is True
        run.assert_called_once_with(["load", LMSTUDIO_MODEL], timeout=120)


def test_ensure_gemma_ready_when_loaded():
    with mock.patch("backend.local_llm.list_loaded_models",
                    return_value=[LMSTUDIO_MODEL]) as listed, \
         mock.patch("backend.local_llm.start_server") as start, \
         mock.patch("backend.local_llm.load_model") as load:
        assert ensure_gemma() is True
        listed.assert_called_once()
        start.assert_not_called()
        load.assert_not_called()


def test_ensure_gemma_starts_when_down():
    with mock.patch("backend.local_llm.list_loaded_models", return_value=[]), \
         mock.patch("backend.local_llm.server_ready", return_value=False), \
         mock.patch("backend.local_llm.start_server", return_value=True), \
         mock.patch("backend.local_llm.load_model", return_value=True) as load:
        assert ensure_gemma() is True
        load.assert_called_once()


# ── chat helpers ─────────────────────────────────────────────────────────

class _ChatResponse:
    status_code = 200

    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.text}}]}


def test_chat_payload_and_result():
    with mock.patch("requests.post", return_value=_ChatResponse("hi there")) as post:
        assert chat("hello", system="be nice") == "hi there"
    body = post.call_args.kwargs["json"]
    assert body["model"] == LMSTUDIO_MODEL
    assert body["messages"][0] == {"role": "system", "content": "be nice"}
    assert body["messages"][1] == {"role": "user", "content": "hello"}
    assert post.call_args.args[0].startswith(LMSTUDIO_API)


def test_chat_error_prefix():
    with mock.patch("requests.post", side_effect=OSError("boom")):
        result = chat("hello")
    assert result.startswith("[ERROR]")


def test_chat_vision_embeds_images():
    fake = _ChatResponse("looks good")
    with mock.patch("requests.post", return_value=fake) as post:
        out = chat_vision({"front": b"\x89PNG-data"}, "what do you see?")
    assert out == "looks good"
    content = post.call_args.kwargs["json"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "what do you see?"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


# ── prompt_builder lmstudio provider ─────────────────────────────────────

def test_ai_assistant_lmstudio_provider_config():
    from backend.ai_assistant import AIAssistant
    a = AIAssistant(provider="lmstudio")
    assert a.base_url == LMSTUDIO_API
    assert a.requires_key is False
    assert a.model == DEFAULT_MODEL


def test_ai_assistant_lmstudio_request_no_key_needed():
    from backend.ai_assistant import AIAssistant
    a = AIAssistant(provider="lmstudio")
    assert a.api_key == ""
    with mock.patch("requests.post", return_value=_ChatResponse("ok")):
        result = a.ask("ping")
    assert result == "ok"


def test_ai_assistant_lmstudio_list_models():
    from backend.ai_assistant import AIAssistant
    a = AIAssistant(provider="lmstudio")
    with mock.patch("requests.get",
                    return_value=_FakeGet([{"id": "google/gemma-4-12b"}])):
        out = a.list_models()
    assert "google/gemma-4-12b" in out


class _FakeGet:
    def __init__(self, data):
        self.data = data

    def json(self):
        return {"data": self.data}


# ── advisor local-first ordering ─────────────────────────────────────────

def test_query_lmstudio_returns_text_when_available():
    with mock.patch("backend.local_llm.server_ready", return_value=True), \
         mock.patch("backend.local_llm.chat", return_value="analysis"):
        from backend.ai_advisor import _query_lmstudio
        assert _query_lmstudio("prompt") == "analysis"


def test_query_lmstudio_none_when_down():
    with mock.patch("backend.local_llm.server_ready", return_value=False), \
         mock.patch("backend.local_llm.ensure_gemma", return_value=False):
        from backend.ai_advisor import _query_lmstudio
        assert _query_lmstudio("prompt") is None


def test_get_llm_suggestion_prefers_lmstudio():
    from backend.ai_advisor import get_llm_suggestion
    result = {"best_candidates": [{"bore_profile": [], "matched_frequencies": [],
                                   "objectives": {}}]}
    with mock.patch("backend.ai_advisor._query_lmstudio", return_value="local") as lm, \
         mock.patch("backend.ai_advisor._query_ollama", return_value="ollama") as ol, \
         mock.patch("backend.ai_advisor._query_openrouter", return_value="or") as o:
        assert get_llm_suggestion(result, [440.0]) == "local"
        lm.assert_called_once()
        ol.assert_not_called()
        o.assert_not_called()


def test_get_llm_suggestion_falls_through_to_ollama_then_openrouter():
    from backend.ai_advisor import get_llm_suggestion
    result = {"best_candidates": [{"bore_profile": [], "matched_frequencies": [],
                                   "objectives": {}}]}
    with mock.patch("backend.ai_advisor._query_lmstudio", return_value=None), \
         mock.patch("backend.ai_advisor._query_ollama", return_value=None), \
         mock.patch("backend.ai_advisor._query_openrouter", return_value="or") as o:
        assert get_llm_suggestion(result, [440.0]) == "or"
        o.assert_called_once()


# ── stl_verifier local-first vision ──────────────────────────────────────

def test_ask_vision_prefers_local():
    from backend import stl_verifier
    with mock.patch("backend.local_llm.server_ready", return_value=True), \
         mock.patch("backend.local_llm.chat_vision",
                    return_value='{"shape": "tube"}') as local:
        out = stl_verifier.ask_vision({"front": b"png"}, "check it")
    assert out == '{"shape": "tube"}'
    local.assert_called_once()


def test_ask_vision_falls_back_to_openrouter_when_local_down():
    from backend import stl_verifier
    with mock.patch("backend.local_llm.server_ready", return_value=False), \
         mock.patch("backend.local_llm.ensure_gemma", return_value=False), \
         mock.patch("requests.post",
                    return_value=_ChatResponse('{"shape": "tube"}')):
        with mock.patch.dict("os.environ", {"OPENROUTER_API_KEY": "k"}):
            out = stl_verifier.ask_vision({"front": b"png"}, "check it")
    assert out == '{"shape": "tube"}'
