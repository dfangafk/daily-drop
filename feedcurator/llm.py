"""LLM provider abstraction for API and local-testing CLI providers."""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable

from litellm import completion

from feedcurator.config import settings

logger = logging.getLogger(__name__)

_CLI_OUTPUT_SCHEMA: str = json.dumps(
    {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "picks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["id", "rationale"],
                },
            },
        },
        "required": ["summary", "picks"],
    }
)


def _call_llm_api(prompt: str) -> str:
    """Invoke an LLM provider API through LiteLLM, trying each model in order.

    Each model is tried with ``num_retries`` (exponential backoff via LiteLLM).
    Moves to the next model if all retries fail.  Raises the last exception if
    all models fail.

    Args:
        prompt: The prompt to send to the configured model.

    Returns:
        JSON string containing ``summary`` and ``picks`` keys.
    """
    if not settings.llm.models:
        raise RuntimeError("LLM_MODELS is required for API provider")

    api_kwargs = dict(settings.llm.api_kwargs)

    last_exc: Exception | None = None
    for m in settings.llm.models:
        try:
            logger.info("Trying LLM model: %s", m)
            response = completion(
                model=m,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                **api_kwargs,
            )
            logger.info("LLM call succeeded with model: %s", m)
            return response.choices[0].message.content
        except Exception as exc:
            logger.warning("Model %s failed after retries: %s", m, exc)
            last_exc = exc

    raise last_exc  # type: ignore[misc]


def _call_claude_cli(prompt: str) -> str:
    """Invoke ``claude -p`` in headless mode and return structured output as JSON.

    Args:
        prompt: The prompt to send to Claude.

    Returns:
        JSON string containing ``summary`` and ``picks`` keys.

    Raises:
        RuntimeError: If the subprocess exits with a non-zero code or if
            ``structured_output`` is absent from the response envelope.
    """
    result = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            _CLI_OUTPUT_SCHEMA,
            "--no-session-persistence",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited with code {result.returncode}: {result.stderr.strip()}"
        )

    response = json.loads(result.stdout)

    if "structured_output" not in response:
        raise RuntimeError(
            f"claude CLI response missing 'structured_output' key: {response!r}"
        )

    return json.dumps(response["structured_output"])


def _call_codex_cli(prompt: str) -> str:
    """Invoke ``codex exec`` in non-interactive mode and return JSON output.

    Args:
        prompt: The prompt to send to Codex.

    Returns:
        JSON string containing ``summary`` and ``picks`` keys.

    Raises:
        RuntimeError: If the subprocess exits with a non-zero code.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    ) as schema_file:
        schema_file.write(_CLI_OUTPUT_SCHEMA)
        schema_path = schema_file.name

    try:
        result = subprocess.run(
            [
                "codex",
                "exec",
                "--ephemeral",
                "--full-auto",
                "--output-schema",
                schema_path,
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
    finally:
        os.unlink(schema_path)

    if result.returncode != 0:
        raise RuntimeError(
            f"codex CLI exited with code {result.returncode}: {result.stderr.strip()}"
        )

    return result.stdout.strip()


def build_complete_fn() -> Callable[[str], str] | None:
    """Return a completion callable backed by API or CLI provider.

    Set ``LLM__PROVIDER`` to explicitly choose a provider:
    ``api``, ``claude_code_cli``, ``codex_cli``, or ``auto`` (default).

    Returns:
        A callable ``(prompt) -> json_str`` or ``None`` if no provider is
        available.
    """
    provider = (settings.llm.provider or "auto").strip().lower()
    if provider not in {"api", "claude_code_cli", "codex_cli", "auto"}:
        logger.warning(
            "Invalid LLM__PROVIDER value '%s'; expected one of: api, claude_code_cli, codex_cli, auto",
            provider,
        )
        return None

    if provider in {"api", "auto"} and settings.llm.models:
        logger.info("Selected LLM provider: API (LLM__MODELS)")
        return _call_llm_api

    if provider in {"claude_code_cli", "auto"} and shutil.which("claude") is not None:
        logger.info("Selected LLM provider: Claude CLI")
        return _call_claude_cli

    if provider in {"codex_cli", "auto"} and shutil.which("codex") is not None:
        logger.info("Selected LLM provider: Codex CLI")
        return _call_codex_cli

    if provider != "auto":
        logger.warning("Requested LLM provider '%s' is not available", provider)
    else:
        logger.info("No LLM provider available")
    return None
