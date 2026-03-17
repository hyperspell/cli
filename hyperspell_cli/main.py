from __future__ import annotations

import typer

from hyperspell_cli import __version__
from hyperspell_cli.commands.auth import app as auth_app
from hyperspell_cli.commands.connections import app as connections_app
from hyperspell_cli.commands.memories import app as memories_app
from hyperspell_cli.commands.search import search

app = typer.Typer(
    name="hyperspell",
    help="Hyperspell CLI - context and memory for AI agents.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    epilog=(
        "[dim]Environment:[/dim]  HYPERSPELL_API_KEY · HYPERSPELL_BASE_URL\n\n"
        "[dim]Output:[/dim]  Human-friendly by default. JSON when piped or with --json."
    ),
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"hyperspell-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Force JSON output (default when stdout is piped).",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress spinners and interactive output; implies --json.",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output or quiet
    ctx.obj["quiet"] = quiet


app.add_typer(auth_app, name="auth")
app.add_typer(memories_app, name="memories")
app.add_typer(connections_app, name="connections")
app.command()(search)


if __name__ == "__main__":
    app()
