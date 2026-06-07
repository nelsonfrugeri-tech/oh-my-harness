"""``omk`` command-line entry point (typer)."""

from __future__ import annotations

from pathlib import Path

import typer

from oh_my_kb.cli.config import (
    UniverseAlreadyExistsError,
    UniverseNotFoundError,
    add_universe,
    load_config,
    save_config,
    set_active,
)
from oh_my_kb.cli.installer import (
    Installer,
    QdrantUnreachableError,
)
from oh_my_kb.cli.paths import default_notes_root_for
from oh_my_kb.services import collection_name_for
from oh_my_kb.storage import QdrantStore, get_qdrant_url

app = typer.Typer(
    name="omk",
    help=(
        "o-kb-client — install, manage universes, expose help. "
        "Knowledge interaction stays in MCP."
    ),
    no_args_is_help=True,
)
universe_app = typer.Typer(
    help="Create, list and switch between universes.",
    no_args_is_help=True,
)
app.add_typer(universe_app, name="universe")


@app.command("help")
def help_cmd(ctx: typer.Context) -> None:
    """Show available commands with a one-line description each."""
    typer.echo(ctx.parent.get_help() if ctx.parent else ctx.get_help())


def _run_harness_selector(active_universe: str) -> None:
    """Interactive harness selector shown at the end of ``omk install``.

    Displays available harnesses (only ``claude-code`` is selectable; the rest
    show as "Coming soon").  If the user picks ``claude-code`` and confirms the
    warning, the bootstrap runs and injects the dynamically-generated rules block
    into ``~/.claude/CLAUDE.md``.  Any other choice or refusal prints a skip
    message and returns without error.
    """
    from oh_my_kb.agents.harness import HARNESS_COMING_SOON, HARNESS_REGISTRY

    selectable = [
        name for name, h in HARNESS_REGISTRY.items()
        if name not in HARNESS_COMING_SOON
    ]
    coming_soon = HARNESS_COMING_SOON

    typer.echo("")
    typer.echo("Which AI assistant do you want to configure?")
    typer.echo("")

    # Build numbered menu — selectable entries first, then coming-soon placeholders
    options: list[tuple[str, bool]] = []
    for name in selectable:
        h = HARNESS_REGISTRY[name]
        label = f"{name:<18} {h.display_label}  ({h.display_path})"
        options.append((label, True))
    for name in coming_soon:
        label = f"{name:<18} Coming soon"
        options.append((label, False))

    for idx, (label, available) in enumerate(options, start=1):
        marker = f"  {idx}." if available else "  -."
        typer.echo(f"{marker} {label}")

    typer.echo("")
    choice_str = typer.prompt(
        "Enter number (or press Enter to skip)", default="", show_default=False
    )
    choice_str = choice_str.strip()

    if not choice_str:
        typer.echo("Nenhum harness configurado. Rode omk bootstrap --harness <name> quando quiser.")
        return

    try:
        choice_idx = int(choice_str) - 1
    except ValueError:
        typer.echo("Entrada inválida. Nenhum harness configurado.")
        return

    if choice_idx < 0 or choice_idx >= len(options):
        typer.echo("Opção fora do range. Nenhum harness configurado.")
        return

    _, available = options[choice_idx]
    if not available:
        typer.echo("Esse harness ainda não está disponível. Nenhum harness configurado.")
        return

    # At this point the user selected a selectable harness (currently only claude-code)
    selected_name = selectable[choice_idx]
    h = HARNESS_REGISTRY[selected_name]
    target_display = h.display_path

    typer.echo("")
    typer.secho(
        "AVISO: Oh My KB vai modificar o seguinte arquivo global:",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    typer.echo("")
    typer.echo(f"   {target_display}")
    typer.echo("")
    typer.echo("   Acao: inserir o bloco de regras do kb-mcp no inicio do arquivo.")
    typer.echo("   O conteudo existente sera preservado.")
    typer.echo("")

    confirmed = typer.confirm("Prosseguir?", default=False)
    if not confirmed:
        typer.echo("Bootstrap cancelado.")
        return

    _do_bootstrap(selected_name, active_universe)


def _do_bootstrap(harness_name: str, active_universe: str) -> None:
    """Run bootstrap and print the report."""
    from oh_my_kb.agents import NoActiveUniverseError, bootstrap
    from oh_my_kb.agents.harness import UnknownHarnessError
    from oh_my_kb.agents.injector import MalformedBlockError

    try:
        report = bootstrap(
            harness=harness_name,
            project_path=Path.cwd(),
            active_universe=active_universe,
        )
    except (
        UnknownHarnessError,
        NoActiveUniverseError,
        MalformedBlockError,
        FileNotFoundError,
    ) as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        return

    action_label = {
        "created": "created",
        "inserted": "inserted",
        "replaced": "updated",
        "unchanged": "already up to date",
    }.get(report.action, report.action)

    typer.secho(
        f"  kb-mcp rules {action_label} for '{report.harness}'.",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo(f"  universe   : {report.universe}")
    typer.echo(f"  target     : {report.target_file}")
    typer.echo(f"  action     : {report.action}")
    typer.echo(f"  bytes      : {report.bytes_written}")


@app.command("install")
def install_cmd() -> None:
    """Bring up Qdrant, ensure the bge-m3 model, create the default universe."""
    try:
        report = Installer().run()
    except QdrantUnreachableError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho("✓ oh-my-kb is ready.", fg=typer.colors.GREEN, bold=True)
    typer.echo("")
    typer.echo("Provisioned:")
    typer.echo(f"  qdrant     : {report.qdrant_url}")
    typer.echo(f"  universe   : {report.universe} (active)")
    typer.echo(f"  notes dir  : {report.notes_root}")
    typer.echo(f"  collection : {report.collection}")
    typer.echo(f"  config     : {report.config_file}")
    typer.echo("")
    typer.echo("Steps:")
    for action in report.actions:
        typer.echo(f"  - {action}")
    typer.echo("")
    typer.echo("Next: write notes via the MCP tool (kb_write) into the active universe.")

    _run_harness_selector(report.universe)


@universe_app.command("create")
def universe_create_cmd(
    name: str = typer.Argument(..., help="Name of the new universe."),
    notes_root: str | None = typer.Option(
        None,
        "--notes-root",
        help="Override the default notes directory (defaults to ~/oh-my-kb/<name>/).",
    ),
) -> None:
    """Create a universe: directory + Qdrant collection + entry in the config."""
    target = (
        default_notes_root_for(name)
        if notes_root is None
        else Path(notes_root).expanduser()
    )
    try:
        cfg = add_universe(load_config(), name=name, notes_root=target)
    except UniverseAlreadyExistsError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    target.mkdir(parents=True, exist_ok=True)
    store = QdrantStore(get_qdrant_url())
    store.ensure_collection(collection_name_for(name))
    save_config(cfg)

    typer.secho(f"✓ universe '{name}' created.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"  notes dir  : {target}")
    typer.echo(f"  collection : {collection_name_for(name)}")


@universe_app.command("list")
def universe_list_cmd() -> None:
    """List configured universes; the active one is marked with ``*``."""
    cfg = load_config()
    if not cfg.universes:
        typer.echo("no universes configured yet. Run `omk install` first.")
        raise typer.Exit(code=0)
    for u in cfg.universes:
        marker = "*" if u.name == cfg.active else " "
        typer.echo(f" {marker} {u.name:20s} {u.collection:24s} {u.notes_root}")


@universe_app.command("use")
def universe_use_cmd(
    name: str = typer.Argument(..., help="Name of the universe to activate."),
) -> None:
    """Set ``name`` as the active universe."""
    try:
        cfg = set_active(load_config(), name)
    except UniverseNotFoundError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    save_config(cfg)
    typer.secho(f"✓ active universe is now '{name}'.", fg=typer.colors.GREEN, bold=True)


@app.command("bootstrap")
def bootstrap_cmd(
    harness: str = typer.Option(
        ...,
        "--harness",
        "-H",
        help="Target harness: claude-code | claude-desktop.",
    ),
    project_path: Path = typer.Option(  # noqa: B008
        None,
        "--project-path",
        "-p",
        help=(
            "Project root where the rules file lives. Defaults to current directory. "
            "Has no effect for global harnesses (e.g. claude-code) — those always "
            "write to their fixed global config path (e.g. ~/.claude/CLAUDE.md)."
        ),
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Inject the kb-mcp rules block into the harness's rules file (idempotent).

    Generates the rules block dynamically from the current MCP tool and resource
    registry, then shows a warning and asks for confirmation before writing to the
    global config file.  Use ``omk bootstrap --harness claude-code`` to regenerate
    the block after adding new tools or resources.
    """
    from oh_my_kb.agents.harness import HARNESS_REGISTRY, UnknownHarnessError

    harness_name = harness.lower()

    try:
        h = HARNESS_REGISTRY[harness_name]
    except KeyError:
        known = ", ".join(sorted(HARNESS_REGISTRY))
        typer.secho(
            f"error: unknown harness '{harness_name}'; known: {known}",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(code=1) from None

    if h.display_path:
        target_display = h.display_path
    elif h.detection_signal:
        target_display = str(Path.home() / h.detection_signal / h.target_filename)
    else:
        target_display = str(Path.home() / h.target_filename)

    typer.echo("")
    typer.secho(
        "AVISO: Oh My KB vai modificar o seguinte arquivo global:",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    typer.echo("")
    typer.echo(f"   {target_display}")
    typer.echo("")
    typer.echo("   Acao: inserir o bloco de regras do kb-mcp no inicio do arquivo.")
    typer.echo("   O conteudo existente sera preservado.")
    typer.echo("")

    confirmed = typer.confirm("Prosseguir?", default=False)
    if not confirmed:
        typer.echo("Bootstrap cancelado.")
        return

    cfg = load_config()
    resolved_path = project_path if project_path is not None else Path.cwd()

    from oh_my_kb.agents import NoActiveUniverseError, bootstrap
    from oh_my_kb.agents.injector import MalformedBlockError

    try:
        report = bootstrap(
            harness=harness_name,
            project_path=resolved_path,
            active_universe=cfg.active,
        )
    except (
        UnknownHarnessError,
        NoActiveUniverseError,
        MalformedBlockError,
        FileNotFoundError,
    ) as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    action_label = {
        "created": "created",
        "inserted": "inserted",
        "replaced": "updated",
        "unchanged": "already up to date",
    }.get(report.action, report.action)

    typer.secho(
        f"  kb-mcp rules {action_label} for '{report.harness}'.",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo(f"  universe   : {report.universe}")
    typer.echo(f"  target     : {report.target_file}")
    typer.echo(f"  action     : {report.action}")
    typer.echo(f"  bytes      : {report.bytes_written}")


@app.command("reindex")
def reindex_cmd(
    universe_name: str | None = typer.Option(
        None,
        "--universe",
        "-u",
        help="Universe to reindex. Defaults to the active universe.",
    ),
) -> None:
    """Reconcile the Qdrant collection with markdown files on disk.

    Scans the universe's notes directory, upserts every .md found (refreshing
    embeddings and correcting paths), and removes Qdrant points whose file no
    longer exists on disk.  Safe to run multiple times — fully idempotent.
    """
    from oh_my_kb.cli.reindex import NoActiveUniverseError, ReindexRunner

    try:
        runner = ReindexRunner()
        report = runner.run(universe_name)
    except NoActiveUniverseError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except UniverseNotFoundError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"scanned {report.scanned} files, upserted {report.upserted} points, "
        f"removed {report.removed} orphans",
        fg=typer.colors.GREEN,
        bold=True,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
