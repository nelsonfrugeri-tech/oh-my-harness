"""Block renderers for the ## Preferências do Usuário section."""

from __future__ import annotations


def render_initial_block(
    now_iso: str,
    system: str,
    machine: str,
    locale: str = "pt-BR",
) -> str:
    """Return the markdown body (without markers) for the initial user-prefs section.

    Args:
        now_iso: UTC datetime in ISO format (e.g. ``"2026-06-11"``).
        system: Operating system name (e.g. ``"Darwin"``).
        machine: Machine hostname (e.g. ``"my-macbook"``).
        locale: Preferred locale tag.  Defaults to ``"pt-BR"``.

    Returns:
        Markdown string — header + base facts, no sentinel markers.
    """
    lines = [
        "## Preferências do Usuário (develop-leap)",
        "",
        f"- SO: {system}",
        f"- Máquina: {machine}",
        f"- Idioma preferido: {locale}",
        f"- Atualizado em: {now_iso}",
    ]
    return "\n".join(lines)


def render_block_with_insights(
    now_iso: str,
    system: str,
    machine: str,
    locale: str,
    insights_md: str,
) -> str:
    """Return the markdown body (without markers) with LLM-extracted insights.

    Args:
        now_iso: UTC datetime in ISO format.
        system: Operating system name.
        machine: Machine hostname.
        locale: Preferred locale tag.
        insights_md: Raw bullet markdown returned by the LLM.

    Returns:
        Markdown string — header + base facts + insights section, no sentinel markers.
    """
    base = render_initial_block(now_iso=now_iso, system=system, machine=machine, locale=locale)
    lines = [
        base,
        "",
        "### Sinais extraídos das sessões",
        "",
        insights_md.strip(),
    ]
    return "\n".join(lines)
