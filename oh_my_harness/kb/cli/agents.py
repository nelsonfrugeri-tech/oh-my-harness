"""``omh kb agents`` — subgroup for managing oh-my-agents (stub).

Subcommands:
    list    — list available agents (stub)
    pull    — download one or all agents (stub)
    diff    — compare local agents with server version (stub)
    update  — apply agent updates (stub)
"""

from __future__ import annotations

import typer

agents_app = typer.Typer(
    help="Manage oh-my-agents (em breve).",
    no_args_is_help=True,
)

_COMING_SOON = "Funcionalidade de agents ainda não implementada. Em breve."


@agents_app.command("list")
def agents_list_cmd() -> None:
    """List available agents."""
    typer.echo(_COMING_SOON)


@agents_app.command("pull")
def agents_pull_cmd(
    name: str | None = typer.Argument(None, help="Agent name."),
    all_agents: bool = typer.Option(False, "--all", help="Pull all agents."),
) -> None:
    """Download one or all agents."""
    typer.echo(_COMING_SOON)


@agents_app.command("diff")
def agents_diff_cmd(
    name: str | None = typer.Argument(None, help="Agent name."),
) -> None:
    """Compare local agents with the current server version."""
    typer.echo(_COMING_SOON)


@agents_app.command("update")
def agents_update_cmd(
    name: str | None = typer.Argument(None, help="Agent name."),
) -> None:
    """Apply agent updates."""
    typer.echo(_COMING_SOON)


__all__ = ["agents_app"]
