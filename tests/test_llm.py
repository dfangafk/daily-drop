"""Tests for feedcurator.llm — provider selection and invocation helpers."""

import json
import subprocess
from pathlib import Path

import pytest

import feedcurator.llm
from feedcurator.llm import (
    _CLI_OUTPUT_SCHEMA,
    _call_claude_cli,
    _call_codex_cli,
    _call_llm_api,
    build_complete_fn,
)


def _patch_llm_settings(mocker, provider, models):
    mocker.patch.object(feedcurator.llm.settings.llm, "provider", provider)
    mocker.patch.object(feedcurator.llm.settings.llm, "models", models)


def test_build_complete_fn_returns_api_fn_when_models_set(mocker):
    _patch_llm_settings(mocker, "auto", ["gemini/gemini-2.5-flash"])
    mock_which = mocker.patch("feedcurator.llm.shutil.which", return_value=None)
    assert build_complete_fn() is _call_llm_api
    mock_which.assert_not_called()


def test_build_complete_fn_returns_api_fn_when_provider_explicitly_api(mocker):
    _patch_llm_settings(mocker, "api", ["gemini/gemini-2.5-flash"])
    mock_which = mocker.patch("feedcurator.llm.shutil.which", return_value=None)
    assert build_complete_fn() is _call_llm_api
    mock_which.assert_not_called()


def test_build_complete_fn_returns_none_when_provider_api_without_models(mocker):
    _patch_llm_settings(mocker, "api", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value="/usr/bin/claude")
    assert build_complete_fn() is None


def test_build_complete_fn_returns_none_when_no_provider_available(mocker):
    _patch_llm_settings(mocker, "auto", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value=None)
    assert build_complete_fn() is None


def test_build_complete_fn_returns_claude_fn_when_claude_on_path(mocker):
    _patch_llm_settings(mocker, "auto", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value="/usr/local/bin/claude")
    result = build_complete_fn()
    assert callable(result)


def test_build_complete_fn_returns_claude_fn_when_provider_explicitly_claude(mocker):
    _patch_llm_settings(mocker, "claude_code_cli", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value="/usr/local/bin/claude")
    assert build_complete_fn() is _call_claude_cli


def test_build_complete_fn_returns_none_when_claude_unavailable(mocker):
    _patch_llm_settings(mocker, "claude_code_cli", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value=None)
    assert build_complete_fn() is None


def test_build_complete_fn_returns_codex_fn_when_codex_on_path(mocker):
    _patch_llm_settings(mocker, "auto", [])
    mocker.patch(
        "feedcurator.llm.shutil.which",
        side_effect=lambda cmd: "/usr/local/bin/codex" if cmd == "codex" else None,
    )
    assert build_complete_fn() is _call_codex_cli


def test_build_complete_fn_returns_codex_fn_when_provider_explicitly_codex(mocker):
    _patch_llm_settings(mocker, "codex_cli", [])
    mocker.patch(
        "feedcurator.llm.shutil.which",
        side_effect=lambda cmd: "/usr/local/bin/codex" if cmd == "codex" else None,
    )
    assert build_complete_fn() is _call_codex_cli


def test_build_complete_fn_returns_none_when_codex_unavailable(mocker):
    _patch_llm_settings(mocker, "codex_cli", [])
    mocker.patch("feedcurator.llm.shutil.which", return_value=None)
    assert build_complete_fn() is None


def test_build_complete_fn_returns_none_on_invalid_provider(mocker):
    _patch_llm_settings(mocker, "bogus", [])
    mock_which = mocker.patch("feedcurator.llm.shutil.which", return_value="/usr/bin/claude")
    assert build_complete_fn() is None
    mock_which.assert_not_called()


def test_call_claude_cli_success(mocker):
    structured = {"summary": "Good picks today.", "picks": [{"id": "https://example.com/a", "rationale": "AI focus."}]}
    envelope = json.dumps({"structured_output": structured})
    mock_run = mocker.patch(
        "feedcurator.llm.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=envelope, stderr=""),
    )

    result = _call_claude_cli("test prompt")

    assert json.loads(result) == structured
    mock_run.assert_called_once()
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "claude"
    assert "-p" in call_args
    assert "test prompt" in call_args


def test_call_claude_cli_raises_on_nonzero_returncode(mocker):
    mocker.patch(
        "feedcurator.llm.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error"),
    )
    with pytest.raises(RuntimeError, match="claude CLI exited with code 1"):
        _call_claude_cli("test prompt")


def test_call_claude_cli_raises_when_structured_output_absent(mocker):
    mocker.patch(
        "feedcurator.llm.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps({"result": "unexpected"}), stderr=""
        ),
    )
    with pytest.raises(RuntimeError, match="missing 'structured_output' key"):
        _call_claude_cli("test prompt")


def test_call_codex_cli_success(mocker):
    mocker.patch("feedcurator.llm.os.unlink")
    mock_run = mocker.patch(
        "feedcurator.llm.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"summary":"S","picks":[]}', stderr=""
        ),
    )

    result = _call_codex_cli("test prompt")

    assert result == '{"summary":"S","picks":[]}'
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "codex"
    assert "--ephemeral" in call_args
    assert "--full-auto" in call_args
    assert "--output-schema" in call_args
    assert "test prompt" in call_args


def test_call_codex_cli_raises_on_nonzero_returncode(mocker):
    mocker.patch(
        "feedcurator.llm.subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error"),
    )
    with pytest.raises(RuntimeError, match="codex CLI exited with code 1"):
        _call_codex_cli("test prompt")


def test_call_llm_api_success(mocker):
    mocker.patch.object(feedcurator.llm.settings.llm, "models", ["gemini/gemini-2.5-flash"])
    mock_completion = mocker.patch("feedcurator.llm.completion")
    mock_completion.return_value = mocker.Mock(
        choices=[mocker.Mock(message=mocker.Mock(content='{"summary":"S","picks":[]}'))]
    )

    result = _call_llm_api("test prompt")

    assert result == '{"summary":"S","picks":[]}'
    mock_completion.assert_called_once_with(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": "test prompt"}],
        response_format={"type": "json_object"},
        num_retries=3,
    )


def test_call_llm_api_raises_when_models_empty(mocker):
    mocker.patch.object(feedcurator.llm.settings.llm, "models", [])
    with pytest.raises(RuntimeError, match="LLM_MODELS is required"):
        _call_llm_api("test prompt")


def test_call_llm_api_falls_back_to_second_model(mocker):
    mocker.patch.object(feedcurator.llm.settings.llm, "models", ["gemini/bad-model", "gemini/gemini-2.5-flash"])
    fallback = '{"summary":"fallback","picks":[]}'
    mock_completion = mocker.patch(
        "feedcurator.llm.completion",
        side_effect=[
            RuntimeError("primary down"),
            mocker.Mock(choices=[mocker.Mock(message=mocker.Mock(content=fallback))]),
        ],
    )

    result = _call_llm_api("test prompt")

    assert result == fallback
    assert mock_completion.call_count == 2


def test_call_llm_api_raises_when_all_models_fail(mocker):
    mocker.patch.object(feedcurator.llm.settings.llm, "models", ["gemini/a", "gemini/b"])
    mocker.patch(
        "feedcurator.llm.completion",
        side_effect=[RuntimeError("a down"), RuntimeError("b down")],
    )
    with pytest.raises(RuntimeError, match="b down"):
        _call_llm_api("test prompt")
