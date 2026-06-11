"""LLM-based preference extraction from curated user prompts."""

from __future__ import annotations

import os
from typing import Any

_SYSTEM_PROMPT = """\
Você é um assistente especializado em extrair preferências do usuário a partir de \
sessões de uso do Claude Code.

Analise as mensagens do usuário abaixo e retorne um resumo conciso em markdown, \
com bullets (linhas começando com "- ") descrevendo as preferências e padrões \
observados.  Foco em:

- idioma preferido de comunicação
- hábitos de editor / estilo de código preferido
- instruções recorrentes dadas ao Claude
- ferramentas e comandos frequentemente solicitados
- qualquer outra preferência pessoal relevante

Responda APENAS com os bullets em português do Brasil — sem título, sem \
introdução, sem explicações adicionais.  Máximo 15 bullets.\
"""


class MissingAnthropicKeyError(ValueError):
    """Raised when ANTHROPIC_API_KEY is missing and no client was provided."""


def extract_preferences(
    curated_prompts: str,
    *,
    client: Any | None = None,
) -> str:
    """Call the Claude API to extract user preferences from *curated_prompts*.

    Args:
        curated_prompts: Concatenated genuine user prompts (output of
            :func:`~oh_my_harness.agents.preferences.sessions.read_recent_user_prompts`).
        client: Optional pre-built ``anthropic.Anthropic`` client.  When
            ``None``, a client is instantiated from
            ``ANTHROPIC_API_KEY`` in the environment.

    Returns:
        The raw assistant text (stripped).  Expected to be a bullet list;
        callers should handle gracefully if the model returns something else.

    Raises:
        MissingAnthropicKeyError: When *client* is ``None`` and
            ``ANTHROPIC_API_KEY`` is not set in the environment.
    """
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise MissingAnthropicKeyError(
                "ANTHROPIC_API_KEY não está configurado no ambiente. "
                "Defina a variável de ambiente antes de usar develop_leap_update."
            )
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": curated_prompts}],
    )

    # The first content block of a non-streaming, non-tool-use response is
    # always a TextBlock.  We guard with getattr to avoid union-attr errors
    # from mypy's strict union narrowing of the Anthropic SDK's typed union.
    first = response.content[0]
    text: str = getattr(first, "text", "")
    return text.strip()
